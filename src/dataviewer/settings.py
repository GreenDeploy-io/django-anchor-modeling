DATAVIEWER_CANONICAL_FIELD_DATA_MAP = {
    "id": {"field": "id", "model": "BusinessEvent"},
    "name": {
        "type": "prefetch_related",
        "field": "value",
        "model": "HistorizedBusinessEventName",
        "order_by": "-from_epoch",
        "related_name": "name",
    },
}
import json

DATAVIEWER_CANONICAL_FIELD_DATA_MAP_IN_JSON = json.dumps(
    DATAVIEWER_CANONICAL_FIELD_DATA_MAP
)
