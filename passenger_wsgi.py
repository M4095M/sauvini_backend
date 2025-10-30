import os
import sys

# Absolute path to this project's backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure project root and apps are on PYTHONPATH
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Point Django to the correct settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sauvini.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()


