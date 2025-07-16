#!/bin/bash
# Start script for Render deployment
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload web_app:app
