"""Composition resources are optional and follow their advertised hierarchy."""

import pytest

from redfish_sdk import RedfishClient
from redfish_sdk.exceptions import RedfishNotFoundError, RedfishValidationError
from redfish_sdk.models.composition import ResourceBlock, ResourceZone
from redfish_sdk.models.root import RootService


@pytest.fixture
def composition_client(monkeypatch):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    root = RootService.model_validate({"CompositionService": {"@odata.id": "/custom/composition"}})
    resources = {
        "/custom/composition": {
            "ServiceEnabled": True, "@odata.id": "/custom/composition",
            "ResourceBlocks": {"@odata.id": "/custom/blocks"},
            "ResourceZones": {"@odata.id": "/custom/zones"},
        },
        "/custom/block/physical": {
            "Id": "block", "@odata.id": "/custom/block/physical", "ResourceBlockType": ["Compute", "Memory"],
            "CompositionStatus": {"CompositionState": "Unused", "SharingCapable": False},
            "Memory": [{"@odata.id": "/custom/dimm"}],
            "Links": {"Zones": [{"@odata.id": "/custom/zone/physical"}]},
        },
        "/custom/zone/physical": {
            "Id": "zone", "@odata.id": "/custom/zone/physical", "ZoneType": "ZoneOfResourceBlocks",
            "Links": {"ResourceBlocks": [{"@odata.id": "/custom/block/physical"}]},
        },
    }
    collections = {"/custom/blocks": "/custom/block/physical", "/custom/zones": "/custom/zone/physical"}
    monkeypatch.setattr(client, "_get_root", lambda: root)
    monkeypatch.setattr(client._http_client, "get", lambda path, model: model.model_validate(resources[path]))
    monkeypatch.setattr(client._http_client, "get_raw", lambda path: {"Members": [{"@odata.id": collections[path]}]})
    yield client
    client.close()


@pytest.mark.parametrize("plural,singular,identifier", [
    ("get_resource_blocks", "get_resource_block", "block"),
    ("get_resource_zones", "get_resource_zone", "zone"),
])
def test_composition_collections_and_members(composition_client, plural, singular, identifier):
    members = getattr(composition_client, plural)()
    assert len(members) == 1
    assert getattr(composition_client, singular)(identifier).odata_id == members[0].odata_id
    assert getattr(composition_client, singular)(members[0].odata_id).id == identifier
    with pytest.raises(RedfishNotFoundError):
        getattr(composition_client, singular)("missing")


def test_composition_core_fields(composition_client):
    assert composition_client.get_composition_service().service_enabled is True
    block = composition_client.get_resource_block("block")
    assert isinstance(block, ResourceBlock)
    assert block.composition_status.sharing_capable is False
    assert block.memory[0].odata_id == "/custom/dimm"
    zone = composition_client.get_resource_zone("zone")
    assert isinstance(zone, ResourceZone)
    assert zone.links.resource_blocks[0].odata_id == block.odata_id
    assert block.links.zones[0].odata_id == zone.odata_id


@pytest.mark.parametrize("payload", [{}, {"CompositionService": {}}])
def test_absent_composition_capability(monkeypatch, payload):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    monkeypatch.setattr(client, "_get_root", lambda: RootService.model_validate(payload))
    with pytest.raises(RedfishNotFoundError, match="CompositionService"):
        client.get_composition_service()
    client.close()


def test_absent_composition_collection(composition_client, monkeypatch):
    service = composition_client.get_composition_service()
    service.resource_blocks = None
    monkeypatch.setattr(composition_client._composition, "get", lambda: service)
    with pytest.raises(RedfishNotFoundError, match="ResourceBlocks"):
        composition_client.get_resource_blocks()


def test_duplicate_resource_ids_require_full_uri(composition_client, monkeypatch):
    first = ResourceBlock.model_validate({"Id": "duplicate", "@odata.id": "/custom/first"})
    second = ResourceBlock.model_validate({"Id": "duplicate", "@odata.id": "/custom/second"})
    monkeypatch.setattr(composition_client._composition, "blocks", lambda: [first, second])
    with pytest.raises(RedfishValidationError, match="Multiple"):
        composition_client.get_resource_block("duplicate")
    assert composition_client.get_resource_block("/custom/first") is first


def test_composition_models_preserve_actions_and_oem():
    block = ResourceBlock.model_validate({"Actions": {"Oem": {"#AMI.Action": {"target": "/custom/action"}}}, "Oem": {"AMI": {"Enabled": True}}})
    assert block.actions["Oem"]["#AMI.Action"]["target"] == "/custom/action"
    assert block.oem["AMI"]["Enabled"] is True
