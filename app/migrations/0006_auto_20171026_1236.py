# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-10-26 07:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_userbrand_mobile_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userbrand',
            name='unit',
        ),
        migrations.AddField(
            model_name='userbrand',
            name='unit',
            field=models.ManyToManyField(blank=True, to='app.BusinessUnit'),
        ),
    ]
