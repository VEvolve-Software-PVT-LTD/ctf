# Generated by Django 2.1.10 on 2019-10-23 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctf', '0008_auto_20191023_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_file_path',
            field=models.CharField(blank=True, default='', max_length=500, null=True, verbose_name='Question File Path'),
        ),
    ]
