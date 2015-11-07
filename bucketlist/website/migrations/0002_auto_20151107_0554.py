# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bucketlist',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='bucketlistitem',
            old_name='bucketlist_id',
            new_name='bucketlist',
        ),
        migrations.RenameField(
            model_name='bucketlistitem',
            old_name='user_id',
            new_name='user',
        ),
    ]
