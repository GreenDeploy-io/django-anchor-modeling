# Generated by Django 4.2.6 on 2023-10-29 00:15

from django.db import migrations, models
import django.db.models.deletion
import django_anchor_modeling.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_anchor_modeling', '0001_initial'),
        ('orders', '0007_tproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductStockQuantity',
            fields=[
                ('value', models.IntegerField(max_length=8)),
                ('anchor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='stock_quantity', serialize=False, to='orders.tproduct')),
                ('transaction', models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductName',
            fields=[
                ('value', models.CharField(max_length=100)),
                ('anchor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='name', serialize=False, to='orders.tproduct')),
                ('transaction', models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductDescription',
            fields=[
                ('value', models.TextField()),
                ('anchor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='description', serialize=False, to='orders.tproduct')),
                ('transaction', models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
