# Generated by Django 5.1.7 on 2025-04-07 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0004_alter_user_options_user_gender_user_phone_user_qq_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='teacher_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
