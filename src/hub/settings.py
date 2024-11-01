import os


DEFAULT_DISTRIBUTION_NAME = 'hub'
DEFAULT_REPOSITORY_NAME = 'hub'

UPLOAD_FOLDER = '/app/uploads'
COLLECTION_UPLOAD_FOLDER = '/app/uploads/collections'

API_HOSTNAME = os.environ.get('API_HOSTNAME', 'http://localhost:8080')
