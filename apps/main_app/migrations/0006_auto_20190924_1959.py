# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-09-24 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0005_bet_game'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bet',
            old_name='closed',
            new_name='paid',
        ),
        migrations.RemoveField(
            model_name='bet',
            name='win',
        ),
        migrations.AddField(
            model_name='bet',
            name='payout',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bet',
            name='result',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]