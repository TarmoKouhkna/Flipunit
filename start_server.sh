#!/bin/bash
# Start Django development server with required environment variables

cd "$(dirname "$0")"

# Google Gemini API Key - set via environment variable
# Set GOOGLE_GEMINI_API_KEY in your environment or .env file before running
# Example: export GOOGLE_GEMINI_API_KEY='your-key-here'

# Set DEBUG to 'True' (as string, which Django expects)
export DEBUG='True'

# Set SECRET_KEY (optional in dev mode when DEBUG=True, but set it anyway)
export SECRET_KEY=${SECRET_KEY:-'django-insecure-dev-key-change-in-production'}

# Start the server
python3 manage.py runserver
