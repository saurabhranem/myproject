# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-10-25 15:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_reason_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbrand',
            name='image_url',
            field=models.ImageField(blank=True, default='profile/profile-default.png', max_length=200, null=True, upload_to=b'profile'),
        ),
    ]
