# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-29 08:43
from __future__ import unicode_literals

import app.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20171129_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='logo',
            field=models.ImageField(blank=True, default='profile/gm.png', max_length=200, null=True, upload_to=app.utils.update_filename),
        ),
    ]
