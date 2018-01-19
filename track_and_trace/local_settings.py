from settings import *

DB_USER = os.environ.get('DB_USER', 'root')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')
DB_PORT = os.environ.get('DB_PORT', '3306')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'shakti',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}