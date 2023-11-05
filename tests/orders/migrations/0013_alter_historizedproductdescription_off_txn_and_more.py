# Generated by Django 4.2.6 on 2023-11-04 10:05

from django.db import migrations, models
import django.db.models.deletion
import django_anchor_modeling.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_anchor_modeling', '0001_initial'),
        ('orders', '0012_alter_historizedproductdescription_off_txn_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historizedproductdescription',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproductdescription',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproducthasseller',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproducthasseller',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproductname',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproductname',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproductstockquantity',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedproductstockquantity',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedtproduct',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedtproduct',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedwithfkthatsetrelatedname',
            name='off_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='deactivated_%(app_label)s_%(class)ss', related_query_name='that_deactivated_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='historizedwithfkthatsetrelatedname',
            name='on_txn',
            field=models.ForeignKey(db_constraint=False, default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_%(app_label)s_%(class)ss', related_query_name='that_created_%(app_label)s_%(class)ss', to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='productdescription',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='producthasseller',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='productname',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='productstockquantity',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='productwithnohistory',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='tproduct',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
        migrations.AlterField(
            model_name='withfkthatsetrelatedname',
            name='transaction',
            field=models.ForeignKey(default=django_anchor_modeling.models.Transaction.get_sentinel_id, on_delete=models.SET(django_anchor_modeling.models.Transaction.get_sentinel), to='django_anchor_modeling.transaction'),
        ),
    ]
