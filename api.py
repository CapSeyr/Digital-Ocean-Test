from flask import Flask, redirect, request
from flask_sqlalchemy import SQLAlchemy 
from flask_restful import Resource, Api, abort 
from marshmallow import Schema, fields, ValidationError 
import string
import random
from datetime import datetime

app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 

db = SQLAlchemy(app) 
api = Api(app) 


class ShortCodeSchema(Schema):
    id = fields.Int(dump_only=True)
    short_code = fields.Str(attribute="code")
    created_at = fields.DateTime()
    click_count = fields.Int()
    original_url = fields.Method("get_original_url")

    def get_original_url(self, obj):
        return obj.url.original_url 

class UrlSchema(Schema):
    id = fields.Int(dump_only = True)
    original_url = fields.Url(required = True)
    custom_alias = fields.Str(load_only=True)
    short_codes = fields.Nested(ShortCodeSchema, many = True, dump_only=True)

url_schema = UrlSchema()
urls_schema = UrlSchema(many = True)
short_code_schema = ShortCodeSchema()
short_codes_schema = ShortCodeSchema(many=True)


class Url(db.Model):
    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)

    #only load if wanted
    short_codes = db.relationship(
        "ShortCode",
        backref="url",
        cascade="all, delete-orphan",
        lazy=True
    )

class ShortCode(db.Model):
    __tablename__ = "short_codes"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(
        db.String(10),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    click_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    url_id = db.Column(
        db.Integer,
        db.ForeignKey("urls.id"),
        nullable=False
    )


class UrlsResource(Resource):
    #return all current Urls in the db
    def get(self):
        urls = Url.query.all() 
        return urls_schema.dump(urls), 200
    
    #add new Url, return shortcode and metadata if possible.
    def post(self):
        json_data = request.get_json()

        try:
            data = url_schema.load(json_data)
        except ValidationError as err:
            return err.messages, 400

        # Reuse existing URL if present
        existing_url = Url.query.filter_by(
            original_url=data["original_url"]
        ).first()

        if existing_url:
            url_obj = existing_url
        else:
            url_obj = Url(original_url=data["original_url"])
            db.session.add(url_obj)
            db.session.flush()

        # Handle a given alias, auto-generate if none
        if data.get("custom_alias"):
            alias = data["custom_alias"]

            if not alias.isalnum():
                return {"error": "Alias must be alphanumeric"}, 400

            if ShortCode.query.filter_by(code=alias).first():
                return {"error": "Alias already in use"}, 400

            short_code_value = alias
        else:
            short_code_value = generate_unique_code()

        # Create short code entry
        new_short_code = ShortCode(
            code=short_code_value,
            url_id=url_obj.id
        )

        db.session.add(new_short_code)
        db.session.commit()

        return {
            "original_url": url_obj.original_url,
            "short_code": short_code_value
        }, 201

class ShortCodeResource(Resource):
    #delete a given shortcode, or parent if this is the only shortcode allocated to it.
    def delete(self, code):
        short_code = ShortCode.query.filter_by(code=code).first()

        if not short_code:
            abort(404, message="Short code not found")

        parent_url = short_code.url

        # If this is the only short code, delete parent instead
        if len(parent_url.short_codes) == 1:
            db.session.delete(parent_url)
        else:
            db.session.delete(short_code)

        db.session.commit()

        return {"message": "Short code deleted successfully"}, 200
    
    #get metadata associated with shortcode
    def get(self, code):
        short_code = ShortCode.query.filter_by(code=code).first_or_404(
            description="Short code not found"
        )

        return short_code_schema.dump(short_code), 200


BASE62 = string.ascii_letters + string.digits
#create random short code
def generate_random_code(length=6):
    return ''.join(random.choices(BASE62, k=length))

#if shortcode already exists try again.
#note, only works small scale. larger scale i would 
#check for integrity errors and then retry.
def generate_unique_code(length=6):
    while True:
        code = generate_random_code(length)
        if not ShortCode.query.filter_by(code=code).first():
            return code
        

#url for posting and getting all urls
api.add_resource(UrlsResource, '/urls')

#url for getting shortcode metadata, and deleting short codes
api.add_resource(ShortCodeResource, "/short/<string:code>")

#redirecting url
@app.route("/<string:code>")
def redirect_short_url(code):
    short_code = ShortCode.query.filter_by(code=code).first_or_404()

    short_code.click_count += 1
    db.session.commit()

    return redirect(short_code.url.original_url)

#landing page, doesnt do much but show that the api is running. 
@app.route("/")
def landing_page():
    return """
    <html>
        <head>
            <title>URL Shortener API</title>
        </head>
        <body>
            <h1>API Landing Page</h1>
            <p>This is the URL Shortener Service.</p>
        </body>
    </html>
    """

if __name__ == '__main__': 
    app.run(debug=True)