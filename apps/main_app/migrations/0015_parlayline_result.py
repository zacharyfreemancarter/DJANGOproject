# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-09-28 02:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0014_auto_20190928_0216'),
    ]

    operations = [
        migrations.AddField(
            model_name='parlayline',
            name='result',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
