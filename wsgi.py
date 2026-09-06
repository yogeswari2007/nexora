"""WSGI entrypoint for production servers (gunicorn / waitress).

Run locally:  gunicorn wsgi:app
"""
import os
from app import app  # noqa: F401  (the Flask application object)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
