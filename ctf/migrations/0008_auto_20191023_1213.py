# Generated by Django 2.1.10 on 2019-10-23 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctf', '0007_auto_20191023_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_file_path',
            field=models.CharField(default='', max_length=500, verbose_name='Question File Path'),
        ),
    ]
