# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-09-26 23:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0007_auto_20190926_2351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='current_quarter',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]