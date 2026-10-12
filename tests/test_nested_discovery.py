"""Nested resources follow advertised links while preserving legacy fallbacks."""

from unittest.mock import Mock

import pytest

from redfish_sdk import RedfishClient
from redfish_sdk.models.managers import Manager
from redfish_sdk.models.systems import System


@pytest.mark.parametrize(
    "method_name,resource_name,parent_kind,collection",
    [
        ("get_memory", "Memory", "Systems", True),
        ("get_bios", "Bios", "Systems", False),
        ("get_network_protocol", "NetworkProtocol", "Managers", False),
        ("get_virtual_media", "VirtualMedia", "Managers", True),
    ],
)
@pytest.mark.parametrize("advertised", [True, False])
def test_nested_resources_use_advertised_links_or_legacy_fallback(
    monkeypatch, method_name, resource_name, parent_kind, collection, advertised
):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    parent_url = f"/redfish/v1/{parent_kind}/Self"
    advertised_url = f"/redfish/v1/custom/{resource_name}"
    payload = {"@odata.id": parent_url, "Id": "Self"}
    if advertised:
        payload[resource_name] = {"@odata.id": advertised_url}
    parent_class = System if parent_kind == "Systems" else Manager
    parent = parent_class.model_validate(payload)
    manager = client._systems if parent_kind == "Systems" else client._managers
    monkeypatch.setattr(manager, "get", lambda identifier=None: parent)
    request = Mock(return_value=[] if collection else object())
    if collection:
        monkeypatch.setattr(client, "_get_collection", request)
    else:
        monkeypatch.setattr(client._http_client, "get", request)

    getattr(client, method_name)()

    assert request.call_args.args[0] == (advertised_url if advertised else f"{parent_url}/{resource_name}")
    client.close()


def test_manager_virtual_media_is_a_typed_link():
    manager = Manager.model_validate({"VirtualMedia": {"@odata.id": "/custom/media"}})
    assert manager.virtual_media.odata_id == "/custom/media"
    assert "VirtualMedia" not in (manager.model_extra or {})


def test_virtual_media_preserves_oem_fallback(monkeypatch):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    manager = Manager.model_validate({
        "@odata.id": "/redfish/v1/Managers/Self",
        "Oem": {"Public": {"VirtualMedia": {"@odata.id": "/custom/oem-media"}}},
    })
    monkeypatch.setattr(client._managers, "get", lambda identifier=None: manager)
    request = Mock(return_value=[])
    monkeypatch.setattr(client, "_get_collection", request)
    client.get_virtual_media()
    assert request.call_args.args[0] == "/custom/oem-media"
    client.close()
