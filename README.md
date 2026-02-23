**URL Shortener Service**

_Overview_

This is a RESTful URL shortener service built with Flask and SQLAlchemy.
It supports automatic short code generation, user-defined custom aliases, redirection, metadata retrieval, and click tracking.

_Features_

Shorten long URLs
Automatically generate unique short codes
Support user-defined custom aliases
Redirect short codes to original URLs
Track click counts
Retrieve metadata for any short code
Support multiple aliases per original URL

_Tech Stack_

Python
Flask
Flask-RESTful
SQLAlchemy
Marshmallow
SQLite (default)

**Data Model**

_Url_

Represents the canonical long URL.

Field	        Type
id	            Integer
original_url	Text

Relationship:

One-to-many with ShortCode

_ShortCode_

Represents a shortened alias.

Field	        Type
id	            Integer
code	        String (Unique, Indexed)
created_at	    DateTime
click_count	    Integer
url_id	        ForeignKey → Url


**API Endpoints**

_Create Short URL_

POST /urls

Request body:

{
  "original_url": "https://example.com",
  "custom_alias": "optionalAlias"
}

Response:

{
  "original_url": "https://example.com",
  "short_code": "abc123"
}
_Get All URLs_

GET /urls

Returns all stored URLs and their associated short codes.

_Get Metadata for Short Code_

GET /short/<code>

Returns:

{
  "id": 1,
  "short_code": "abc123",
  "created_at": "2026-02-23T20:14:32",
  "click_count": 10,
  "original_url": "https://example.com"
}

_Delete Short Code_

DELETE /short/<code>

Deletes a short code.
If it is the only short code for a URL, the URL is deleted as well.

_Redirect_

GET /<code>

Redirects to the original URL and increments click count.

Running Locally
pip install -r requirements.txt
python api.py

Server runs at:

http://127.0.0.1:5000
typical localhost for this interview.

Design Decisions

URLs are normalized to prevent duplication.
Multiple short codes can point to the same original URL.
Short codes are randomly generated using Base62.
Click counts are tracked per short code.
Database-level uniqueness ensures no duplicate aliases.
