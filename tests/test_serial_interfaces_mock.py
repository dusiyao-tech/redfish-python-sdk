"""SerialInterface discovery, advertised constraints, and conditional PATCH."""

import json
from unittest.mock import Mock

import pytest
import requests

from redfish_sdk import RedfishClient
from redfish_sdk.exceptions import RedfishNotFoundError, RedfishValidationError
from redfish_sdk.models.managers import Manager, SerialInterface


@pytest.fixture
def serial_client(monkeypatch):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    manager = Manager.model_validate({"Id": "Self", "SerialInterfaces": {"@odata.id": "/custom/serial"}})
    payload = {
        "Id": "IPMI-SOL", "@odata.id": "/custom/sol", "@odata.etag": '"serial-etag"',
        "InterfaceEnabled": True, "BitRate": "115200", "DataBits": "8", "Parity": "None",
        "BitRate@Redfish.AllowableValues": ["9600", "115200"],
        "Actions": {"Oem": {}}, "Oem": {"AMI": {"Sol": True}},
    }
    monkeypatch.setattr(client._managers, "get", lambda identifier=None: manager)
    monkeypatch.setattr(client._http_client, "get_raw", lambda path: {"Members": [{"@odata.id": "/custom/sol"}]} if path == "/custom/serial" else pytest.fail(path))

    def request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/custom/sol"
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(payload).encode()
        response.headers["ETag"] = '"serial-etag"'
        return response

    monkeypatch.setattr(client._http_client, "_request", request)
    yield client, manager
    client.close()


def test_serial_list_and_get_follow_links(serial_client):
    client, _ = serial_client
    interface = client.get_serial_interfaces()[0]
    assert isinstance(interface, SerialInterface)
    assert interface.bit_rate == "115200"
    assert interface.actions == {"Oem": {}}
    assert interface.oem["AMI"]["Sol"] is True
    assert client.get_serial_interface("IPMI-SOL").odata_id == "/custom/sol"
    assert client.get_serial_interface("/custom/sol").id == "IPMI-SOL"
    assert client.get_serial_interface().id == "IPMI-SOL"
    with pytest.raises(RedfishNotFoundError):
        client.get_serial_interface("missing")


def test_serial_patch_uses_only_supplied_fields_and_etag(serial_client, monkeypatch):
    client, _ = serial_client
    original_request = client._http_client._request
    calls = []

    def request(method, path, **kwargs):
        if method == "GET":
            return original_request(method, path, **kwargs)
        calls.append((method, path, kwargs))
        response = requests.Response()
        response.status_code = 204
        response._content = b""
        return response

    monkeypatch.setattr(client._http_client, "_request", request)
    client.update_serial_interface("IPMI-SOL", interface_enabled=False, bit_rate="9600")
    method, path, arguments = calls[0]
    assert (method, path) == ("PATCH", "/custom/sol")
    assert arguments["json"] == {"InterfaceEnabled": False, "BitRate": "9600"}
    assert arguments["headers"]["If-Match"] == '"serial-etag"'


def test_serial_patch_rejects_unsupported_rate(serial_client, monkeypatch):
    client, _ = serial_client
    patch = Mock()
    monkeypatch.setattr(client._http_client, "patch", patch)
    with pytest.raises(RedfishValidationError, match="BitRate"):
        client.update_serial_interface("IPMI-SOL", bit_rate="57600")
    patch.assert_not_called()
    with pytest.raises(RedfishValidationError, match="at least one"):
        client.update_serial_interface("IPMI-SOL")


def test_absent_optional_serial_collection(serial_client):
    client, manager = serial_client
    manager.serial_interfaces = None
    with pytest.raises(RedfishNotFoundError, match="SerialInterfaces"):
        client.get_serial_interfaces()


def test_ambiguous_serial_identifier(serial_client, monkeypatch):
    client, _ = serial_client
    first = SerialInterface.model_validate({"Id": "IPMI-SOL", "@odata.id": "/custom/one"})
    second = SerialInterface.model_validate({"Id": "IPMI-SOL", "@odata.id": "/custom/two"})
    monkeypatch.setattr(client._managers, "serial_interfaces", lambda manager_id=None: [first, second])
    with pytest.raises(RedfishValidationError, match="Multiple"):
        client.get_serial_interface()
    with pytest.raises(RedfishValidationError, match="Multiple"):
        client.get_serial_interface("IPMI-SOL")
    assert client.get_serial_interface("/custom/two") is second
