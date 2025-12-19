#!/bin/bash
# Start Django development server with required environment variables

cd "$(dirname "$0")"

# Set Google Gemini API Key
export GOOGLE_GEMINI_API_KEY='AIzaSyAwqWBmAImLYZKRk2IvrW2ZqSN_wCgrArY'

# Set DEBUG to 'True' (as string, which Django expects)
export DEBUG='True'

# Set SECRET_KEY (optional in dev mode when DEBUG=True, but set it anyway)
export SECRET_KEY=${SECRET_KEY:-'django-insecure-dev-key-change-in-production'}

# Start the server
python3 manage.py runserver
