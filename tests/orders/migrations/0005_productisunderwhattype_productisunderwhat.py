# Generated by Django 4.2.6 on 2023-10-25 18:18

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_ordertypetextchoicesnochoices_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductIsUnderWhatType',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductIsUnderWhat',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator(message='ID must be alphanumeric, underscores, hyphens, and dots.', regex='^[0-9a-zA-Z_.-]+$')])),
                ('under_what_id', models.PositiveIntegerField()),
                ('under_what_type', models.CharField(choices=[('ORDERS__ORDER', 'Order'), ('ORDERS__ORDER_LINE_ITEM', 'Order Line Item')], max_length=100)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='is_under', to='orders.product')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
