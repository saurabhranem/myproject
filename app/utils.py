import os
from uuid import uuid4

from django.conf import settings


def update_filename(instance, filename):
    return os.path.join(settings.PROFILE_LOCATION,
                        "{}-{}.{}".format(instance.user_id,
                                          uuid4().hex,
                                          filename.split('.')[-1]))


def update_logo(instance, filename):
    return os.path.join(settings.PROFILE_LOCATION,
                        "{}.{}".format(uuid4().hex,
                                          filename.split('.')[-1]))