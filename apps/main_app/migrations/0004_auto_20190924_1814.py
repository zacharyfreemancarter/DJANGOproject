# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-09-24 18:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0003_auto_20190924_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bet',
            name='win',
            field=models.BooleanField(default=False),
        ),
    ]
