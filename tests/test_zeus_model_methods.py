import pytest
from django.test import TestCase

from tests.orders.models import RegularThreeNFModelUsingZeUS


@pytest.mark.django_db
class TestZeusUsingModel(TestCase):
    def test_save_when_pk_not_none(self):
        # Create a instance that extends ZeUS
        obj_1 = RegularThreeNFModelUsingZeUS.objects.create(name="old name")
        pk = obj_1.id
        old_name = obj_1.name

        # Update the name
        obj_1.name = "new name"
        obj_1.save()

        # Assert new instance is created and old one is deleted
        assert RegularThreeNFModelUsingZeUS.objects.count() == 1
        # same database rows since ZeUS
        assert obj_1.id == pk
        assert obj_1.name != old_name
