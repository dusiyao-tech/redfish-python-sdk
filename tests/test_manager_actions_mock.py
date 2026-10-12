"""Manager reset and log clearing use advertised actions and resource links."""

from unittest.mock import Mock

import pytest

from redfish_sdk import RedfishClient
from redfish_sdk.exceptions import RedfishNotFoundError, RedfishValidationError
from redfish_sdk.models.common import RedfishResponse
from redfish_sdk.models.managers import Manager


@pytest.fixture
def manager_client(monkeypatch):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    manager = Manager.model_validate({
        "Id": "Self", "@odata.id": "/redfish/v1/Managers/Self",
        "LogServices": {"@odata.id": "/custom/services"},
        "Actions": {"#Manager.Reset": {"target": "/custom/restart", "ResetType@Redfish.AllowableValues": ["ForceRestart"]}},
    })
    services = {
        f"/custom/log/{identifier}": {"Id": identifier, "@odata.id": f"/custom/log/{identifier}", "Actions": {"#LogService.ClearLog": {"target": f"/custom/clear/{identifier}"}}}
        for identifier in ["AuditLog", "SEL", "EventLog"]
    }
    monkeypatch.setattr(client._managers, "get", lambda manager_id=None: manager)
    monkeypatch.setattr(client._http_client, "get_raw", lambda path: {"Members": [{"@odata.id": member} for member in services]} if path == "/custom/services" else pytest.fail(path))
    monkeypatch.setattr(client._http_client, "get", lambda path, model: model.model_validate(services[path]))
    post = Mock(return_value=RedfishResponse())
    monkeypatch.setattr(client._http_client, "post", post)
    yield client, manager, services, post
    client.close()


def test_manager_reset_uses_advertised_target(manager_client):
    client, _, _, post = manager_client
    assert isinstance(client.reset_manager(), RedfishResponse)
    post.assert_called_once_with("/custom/restart", RedfishResponse, raw_body={"ResetType": "ForceRestart"})


def test_manager_reset_rejects_unsupported_types(manager_client):
    client, _, _, post = manager_client
    with pytest.raises(RedfishValidationError, match="ResetType"):
        client.reset_manager("GracefulRestart")
    post.assert_not_called()


@pytest.mark.parametrize("actions", [None, {}, {"#Manager.Reset": {}}, {"#Manager.Reset": {"target": 7}}])
def test_missing_manager_reset_action(manager_client, actions):
    client, manager, _, post = manager_client
    manager.actions = actions
    with pytest.raises(RedfishValidationError, match="Manager.Reset"):
        client.reset_manager()
    post.assert_not_called()


def test_manager_reset_action_info_validation(manager_client, monkeypatch):
    client, manager, _, post = manager_client
    manager.actions = {"#Manager.Reset": {"target": "/custom/restart", "@Redfish.ActionInfo": "/custom/reset-info"}}
    monkeypatch.setattr(client._http_client, "get_raw", lambda path: {"Parameters": [{"Name": "ResetType", "AllowableValues": ["GracefulRestart"]}]} if path == "/custom/reset-info" else pytest.fail(path))
    with pytest.raises(RedfishValidationError):
        client.reset_manager()
    client.reset_manager("GracefulRestart")
    assert post.call_args.kwargs["raw_body"] == {"ResetType": "GracefulRestart"}


@pytest.mark.parametrize("identifier", ["AuditLog", "SEL", "EventLog"])
def test_manager_log_lookup_and_clear(manager_client, identifier):
    client, _, _, post = manager_client
    log = client.get_manager_log_service(identifier)
    assert log.odata_id == f"/custom/log/{identifier}"
    assert client.get_manager_log_service(log.odata_id).id == identifier
    client.clear_manager_log(identifier)
    post.assert_called_once_with(f"/custom/clear/{identifier}", RedfishResponse, raw_body={})


def test_missing_clear_action_does_not_mutate(manager_client):
    client, _, services, post = manager_client
    services["/custom/log/SEL"]["Actions"] = {}
    with pytest.raises(RedfishValidationError, match="ClearLog"):
        client.clear_manager_log("SEL")
    post.assert_not_called()


def test_ambiguous_or_missing_manager_log(manager_client):
    client, _, _, post = manager_client
    with pytest.raises(RedfishValidationError, match="Multiple"):
        client.get_manager_log_service()
    with pytest.raises(RedfishNotFoundError):
        client.clear_manager_log("missing")
    post.assert_not_called()


def test_sole_manager_log_can_be_selected_automatically(manager_client):
    client, _, services, post = manager_client
    services.pop("/custom/log/AuditLog")
    services.pop("/custom/log/EventLog")
    client.clear_manager_log()
    post.assert_called_once_with("/custom/clear/SEL", RedfishResponse, raw_body={})
