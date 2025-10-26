Create Virtual Environment and Install Dependencies# Create and activate environment
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
# NOTE: django-filter is required for the filtering configuration to work correctly.
pip install django djangorestframework requests django-filter


B. Create Django Project and App# Create the main project
django-admin startproject wikipedia_project

# Move into the project directory
cd wikipedia_project

# Create the application that handles streaming and APIs
# Note: Renamed to avoid name conflict with common Python module names.
python manage.py startapp wiki_stream_app


C. Configure SettingsIn wikipedia_project/settings.py, register the app and DRF:# wikipedia_project/settings.py

INSTALLED_APPS = [
    # ... other default apps
    'rest_framework',
    'django_filters', # MUST be added when using DEFAULT_FILTER_BACKENDS
    'wiki_stream_app',
]

# (Optional) Add REST Framework configuration for better browsing
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50
}


D. Apply Initial Migrationspython manage.py makemigrations wiki_stream_app
python manage.py migrate


3. Implement Stream Processor (Management Command)Place the provided code for capture_stream.py into the following directory structure:wikipedia_project/wiki_stream_app/management/commands/capture_stream.py4. Implement API and ModelsPlace the provided code for models.py, api_views.py, and urls.py into the wikipedia_project/wiki_stream_app/ directory.5. Configure Main Project URLsIn wikipedia_project/urls.py, include the app's URLs:# wikipedia_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/edits/', include('wiki_stream_app.urls')),
]


6. Running the ApplicationStep 1: Start the Django Web Server (API)In your first terminal session:python manage.py runserver


The API will now be accessible at http://127.0.0.1:8000/api/edits/...Step 2: Run the Real-Time Stream Capture WorkerThe stream capture must be run as a separate, long-running process.In your second terminal session, use the custom management command:# This command defaults to 10 minutes (600 seconds)
python manage.py capture_stream

# To run for 1 hour (3600 seconds):
python manage.py capture_stream --duration 3600

# To run for 24 hours (86400 seconds):
# python manage.py capture_stream --duration 86400


The worker will now connect to the Wikimedia stream and save processed edits to the database for the specified duration.
