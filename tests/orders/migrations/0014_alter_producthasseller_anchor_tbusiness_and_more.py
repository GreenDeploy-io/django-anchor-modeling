# Generated by Django 4.2.6 on 2023-11-05 11:00

from django.db import migrations, models
import django.db.models.deletion
import django_anchor_modeling.fields
import django_anchor_modeling.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_anchor_modeling', '0001_initial'),
        ('orders', '0013_alter_historizedproductdescription_off_txn_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producthasseller',
            name='anchor',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='seller', serialize=False, to='orders.tproduct'),
        ),
        migrations.CreateModel(
            name='TBusiness',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_identifier', django_anchor_modeling.fields.BusinessIdentifierField(max_length=255, unique=True)),
                ('transaction', models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='historizedproducthasseller',
            name='value',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='orders.tbusiness'),
        ),
        migrations.AlterField(
            model_name='producthasseller',
            name='value',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='orders.tbusiness'),
        ),
    ]
