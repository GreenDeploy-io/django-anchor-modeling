import logging

import pytest
from django.apps import apps
from django.db import transaction as db_transaction
from django.test import TestCase

from dataviewer.models import BusinessToQueryMap
from dataviewer.utils.query_capture_handler import QueryCaptureHandler
from dataviewer.utils.query_helpers import QueryHelpers
from django_anchor_modeling.models import Transaction
from tests.orders.models.dataviewer_models import (
    Child,
    ChildName,
    ChildParent,
    Grandchild,
    GrandchildName,
    GrandchildParent,
    Grandparent,
    GrandparentName,
    Parent,
    ParentName,
    ParentParent,
)

HistorizedGrandparent = apps.get_model("orders", "HistorizedGrandparent")
import time


@pytest.mark.django_db
class TestDataViewerModel(TestCase):
    """
    total got 10 use cases:
    1. get single grandparent
        1. grandparent as main model get parent, child, and grandchild with name as attributes
    2. get multiple grandparents
        1. grandparent as main model get parent, child, and grandchild with name as attributes
    3. get flat dict of single grandparent with list of parents with id, and name
           and list of parents with name as comma-delimited string
    4. repeat 3 but is list of flat dict of multiple grandparents

    exceptions:
    1. ActiveModelClassMustBeTransactionBackedError TE001
    2. CannotReuseExistingTransactionError TE002
    3. MissingTransactionInModelError TE003
    4. SentinelTransactionCannotBeUsedError TE004
    """

    def setUp(self):
        """
        setup a default p0
        """
        with db_transaction.atomic():
            t0 = Transaction.objects.create()
            self.gp0 = Grandparent.objects.create(
                business_identifier="gp0", transaction=t0
            )
            GrandparentName.objects.create(
                anchor=self.gp0, value="Grandparent 0", transaction=t0
            )

            self.p0 = Parent.objects.create(transaction=t0)
            ParentName.objects.create(anchor=self.p0, value="Parent 0", transaction=t0)

            ParentParent.objects.create(anchor=self.p0, value=self.gp0, transaction=t0)

            c0 = Child.objects.create(transaction=t0)
            ChildName.objects.create(anchor=c0, value="Child 0", transaction=t0)

            ChildParent.objects.create(anchor=c0, value=self.p0, transaction=t0)

            gc0 = Grandchild.objects.create(transaction=t0)
            GrandchildName.objects.create(
                anchor=gc0, value="Grandchild 0", transaction=t0
            )

            GrandchildParent.objects.create(anchor=gc0, value=c0, transaction=t0)

            BusinessToQueryMap.objects.create(
                pk="WHOLE_TREE",
                description="whole tree",
                main_model_class="orders.Grandparent",
                select_related=["name"],
                # select_related=[],
                prefetch_related=[
                    # {
                    #     "prefetch_field": "name",
                    #     "model": "orders.GrandparentName",
                    #     "is_one_to_one": True,
                    # },
                    {
                        "prefetch_field": "parentparent_set",
                        "model": "orders.ParentParent",
                        "only_fields": ["pk", "value_id"],
                        "nested_prefetch": [
                            {
                                "prefetch_field": "anchor",
                                "model": "orders.Parent",
                                "only_fields": [
                                    "id",
                                ],
                                "is_one_to_one": True,
                                "nested_prefetch": [
                                    {
                                        "prefetch_field": "name",
                                        "model": "orders.ParentName",
                                        "only_fields": [
                                            "value",
                                        ],
                                        "is_one_to_one": True,
                                    }
                                ],
                            }
                        ],
                    },
                ],
                only=[
                    "id",
                    "business_identifier",
                    "name__value"
                    # "parentparent_set__anchor__id",
                    # "parent_set__name__value",
                    # "parent_set__child_set__id",
                    # "parent_set__child_set__name__value",
                    # "parent_set__child_set__grandchild_set__id",
                    # "parent_set__child_set__grandchild_set__name__value",
                ],
                field_processors={
                    "id": {
                        "field": "id",
                        # "condition": "hasattr",
                        # "attribute": "quotation",
                        # "sub_field": "value.display_quotation_number"
                    },
                    "business_identifier": {
                        "field": "business_identifier",
                    },
                    "name": {
                        "field": "name",
                        "condition": "hasattr",
                        "attribute": "name",
                        "sub_field": "value",
                    },
                },
            )

    def _create_grandparents(self, times: int, transaction):
        """
        times is number of grandparent to create
        """
        # i need epoch timestamp as integer
        epoch = int(time.time())
        results = []
        for i in range(times):
            gp = Grandparent.objects.create(
                business_identifier=f"gp{epoch} - {i}", transaction=transaction
            )
            GrandparentName(
                anchor=gp, value=f"Grandparent {i}", transaction=transaction
            )
            results.append(gp)
        return results

    def _create_parents(self, grandparents, times: int, transaction):
        """
        times is number of parents to create per grandparent
        """
        parents = []
        for gp in grandparents:
            for i in range(times):
                p = Parent.objects.create(transaction=transaction)
                ParentName(
                    anchor=p, value=f"Parent {gp.id} - {i}", transaction=transaction
                )
                ParentParent.objects.create(anchor=p, value=gp, transaction=transaction)
                parents.append(p)
        return parents

    def _create_children(self, parents, times: int, transaction):
        """
        times is number of children to create per parent
        """
        children = []
        for p in parents:
            for i in range(times):
                c = Child.objects.create(transaction=transaction)
                ChildName(
                    anchor=p, value=f"Child {p.id} - {i}", transaction=transaction
                )
                ChildParent.objects.create(anchor=c, value=p, transaction=transaction)
                children.append(c)

    def _create_grandchildren(self, children, times: int, transaction):
        """
        times is number of grandchildren to create per child
        """
        grandchildren = []
        for c in children:
            for i in range(times):
                gc = Grandchild.objects.create(transaction=transaction)
                GrandchildName(
                    anchor=c, value=f"Grandchild {c.id} - {i}", transaction=transaction
                )
                GrandchildParent.objects.create(
                    anchor=gc, value=c, transaction=transaction
                )
                grandchildren.append(gc)
        return grandchildren

    def test_field_processors_are_working_and_query_count_is_ok(self):
        # sourcery skip: extract-duplicate-method, inline-immediately-returned-variable
        """
        happy path
        let's just fetch the whole tree in setUp
        """
        query_capture_handler = QueryCaptureHandler()
        logger = logging.getLogger("django.db.backends")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(query_capture_handler)

        expected_queries = (
            1  # the one for BusinessToQueryMap.objects.get(pk="WHOLE_TREE")
        )
        expected_queries += 1  # the one for count()
        expected_queries += (
            1  # the INNER between parentparent and parent with no where clause
        )
        expected_queries += 1  # the LEFT OUTER JOIN between grandparent and grandparentname to get the name
        expected_queries += 1  # the INNER join between parentparent and parent where parentparent.value_id IN (1)
        expected_queries += 1  # the one for getting parentname by parent

        with self.assertNumQueries(6):
            bdmap = BusinessToQueryMap.objects.get(pk="WHOLE_TREE")
            main_model = QueryHelpers._get_model_for_queryset(bdmap.main_model_class)
            queryset = main_model.objects

            assert 1 == queryset.count()

            select_related = bdmap.select_related
            prefetch_related = bdmap.prefetch_related
            only = bdmap.only

            # apply select_related
            queryset = queryset.select_related(*select_related)

            # apply prefetch_related
            queryset = QueryHelpers.apply_nested_prefetch_rules(
                queryset, prefetch_related
            )

            print(select_related)
            print(prefetch_related)
            print(only)

            queryset = queryset.only(*only)

            grandparents = list(queryset.all())

            grandparent_list = []

            for grandparent in grandparents:
                # Start with the main model's fields
                grandparent_dict = {
                    "id": grandparent.id,
                    "business_identifier": grandparent.business_identifier,
                    "name": grandparent.name.value,
                    "parents": [],
                }
                parents = grandparent.parentparent_set.all()
                for p in parents:
                    grandparent_dict["parents"].append(
                        {
                            "id": p.pk,
                            "name": p.anchor.name.value,
                        }
                    )

                grandparent_list.append(grandparent_dict)

            print(grandparent_list)

            # Detach the handler and reset logging level
            logger.removeHandler(query_capture_handler)
            logger.setLevel(logging.NOTSET)

            for query in query_capture_handler.queries:
                print(query)  # Or perform your assertions here

            processed_list = []
            for grandparent in grandparents:
                processed = QueryHelpers.process_instance(
                    grandparent, bdmap.field_processors
                )
                processed_list.append(processed)
            assert processed_list == [
                {
                    "id": self.gp0.id,
                    "business_identifier": self.gp0.business_identifier,
                    "name": self.gp0.name.value,
                }
            ]

    def test_get_children_as_list_and_str(self):
        """
        get back the parents as comma-delimited str of names and list
        """
        t1 = Transaction.objects.create()
        self.p1 = Parent.objects.create(transaction=t1)
        ParentName.objects.create(anchor=self.p1, value="Parent 1", transaction=t1)

        ParentParent.objects.create(anchor=self.p1, value=self.gp0, transaction=t1)

        BusinessToQueryMap.objects.create(
            pk="ONE_GP_WITH_PARENTS",
            description="one GP with parents",
            main_model_class="orders.Grandparent",
            select_related=["name"],
            # select_related=[],
            prefetch_related=[
                # {
                #     "prefetch_field": "name",
                #     "model": "orders.GrandparentName",
                #     "is_one_to_one": True,
                # },
                {
                    "prefetch_field": "parentparent_set",
                    "model": "orders.ParentParent",
                    "only_fields": ["pk", "value_id"],
                    "nested_prefetch": [
                        {
                            "prefetch_field": "anchor",
                            "model": "orders.Parent",
                            "only_fields": [
                                "id",
                            ],
                            "is_one_to_one": True,
                            "nested_prefetch": [
                                {
                                    "prefetch_field": "name",
                                    "model": "orders.ParentName",
                                    "only_fields": [
                                        "value",
                                    ],
                                    "is_one_to_one": True,
                                }
                            ],
                        }
                    ],
                },
            ],
            only=[
                "id",
                "business_identifier",
                "name__value",
                # "parentparent_set__anchor__id",
                # "parentparent_set__anchor__name__value",
            ],
            field_processors={
                "id": {
                    "field": "id",
                    # "condition": "hasattr",
                    # "attribute": "quotation",
                    # "sub_field": "value.display_quotation_number"
                },
                "business_identifier": {
                    "field": "business_identifier",
                },
                "name": {
                    "field": "name",
                    "condition": "hasattr",
                    "attribute": "name",
                    "sub_field": "value",
                },
                "parents": {
                    "field": "parentparent_set",
                    "attributes": {
                        "id": "anchor.id",
                        "name": "anchor.name.value",
                    },
                },
                "parent_names_string": {
                    "field": "parentparent_set",
                    "attributes": {
                        "name": "anchor.name.value",
                    },
                    "format": "string",  # This will return a comma-delimited string
                },
            },
        )

        bdmap = BusinessToQueryMap.objects.get(pk="ONE_GP_WITH_PARENTS")
        main_model = QueryHelpers._get_model_for_queryset(bdmap.main_model_class)
        queryset = main_model.objects

        assert 1 == queryset.count()

        select_related = bdmap.select_related
        prefetch_related = bdmap.prefetch_related
        only = bdmap.only

        # apply select_related
        queryset = queryset.select_related(*select_related)

        # apply prefetch_related
        queryset = QueryHelpers.apply_nested_prefetch_rules(queryset, prefetch_related)

        print(select_related)
        print(prefetch_related)
        print(only)

        queryset = queryset.only(*only)

        grandparents = queryset.all()

        processed_list = []
        for grandparent in grandparents:
            processed = QueryHelpers.process_instance(
                grandparent, bdmap.field_processors
            )
            processed_list.append(processed)

        assert processed_list == [
            {
                "id": self.gp0.id,
                "business_identifier": self.gp0.business_identifier,
                "name": self.gp0.name.value,
                "parents": [
                    {
                        "id": self.p0.id,
                        "name": self.p0.name.value,
                    },
                    {
                        "id": self.p1.id,
                        "name": self.p1.name.value,
                    },
                ],
            }
        ]
