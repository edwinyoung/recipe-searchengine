# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-01 23:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('searchengine', '0005_auto_20170429_0117'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipe',
            old_name='ingredients',
            new_name='ingredient',
        ),
    ]
