# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-29 07:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20171028_1723'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='brand',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Brand'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuedstocks',
            name='brand',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Brand'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productcount',
            name='brand',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Brand'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reason',
            name='brand',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Brand'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stocks',
            name='brand',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Brand'),
            preserve_default=False,
        ),
    ]
