# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-09-27 15:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0009_auto_20190927_1539'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='total_coints',
            new_name='total_coins',
        ),
    ]
