# Generated by Django 4.2.6 on 2023-10-24 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_regularthreenfmodelusingzeus'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderType',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
