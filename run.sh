#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:8000 app:app --workers 4 --timeout 120