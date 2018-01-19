from settings import *

DB_USER = os.environ.get('DB_USER', 'gladminds')
DB_HOST = os.environ.get('DB_HOST', 'gladminds-qa-2.chnnvvffqwop.us-east-1.rds.amazonaws.com')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'gladmindsqa2')
DB_PORT = os.environ.get('DB_PORT', '3306')

DEBUG = False

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