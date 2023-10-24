# Generated by Django 4.2.6 on 2023-10-18 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataChangeReason',
            fields=[
                ('value', models.TextField()),
                ('anchor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='reason', serialize=False, to='metadata.datachange')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]