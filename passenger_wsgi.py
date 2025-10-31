import os
import sys

# Path to your Django project (update if different)
BASE_DIR = '/home/sauvini/repositories/sauvini_backend'

# Add project directory to sys.path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sauvini.settings')

# Activate virtual environment (if you created one)
VENV_PATH = '/home/sauvini/virtualenv/sauvini_backend/3.13/bin/activate_this.py'
if os.path.exists(VENV_PATH):
    with open(VENV_PATH) as f:
        exec(f.read(), {'__file__': VENV_PATH})

# Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
