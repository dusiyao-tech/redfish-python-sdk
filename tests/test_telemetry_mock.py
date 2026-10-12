"""Telemetry discovery works without assuming vendor resource paths."""

import pytest

from redfish_sdk import RedfishClient
from redfish_sdk.exceptions import RedfishNotFoundError, RedfishValidationError
from redfish_sdk.models.root import RootService
from redfish_sdk.models.telemetry import MetricReport, MetricReportDefinition


@pytest.fixture
def telemetry_client(monkeypatch):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    root = RootService.model_validate({"TelemetryService": {"@odata.id": "/custom/telemetry"}})
    resources = {
        "/custom/telemetry": {
            "@odata.id": "/custom/telemetry", "ServiceEnabled": True,
            "MetricDefinitions": {"@odata.id": "/custom/definitions"},
            "MetricReportDefinitions": {"@odata.id": "/custom/report-definitions"},
            "MetricReports": {"@odata.id": "/custom/reports"},
            "Triggers": {"@odata.id": "/custom/triggers"},
            "LogService": {"@odata.id": "/custom/log"},
        },
        "/custom/member/definition": {"@odata.id": "/custom/member/definition", "Id": "temperature", "Units": "Cel"},
        "/custom/member/report-definition": {"@odata.id": "/custom/member/report-definition", "Id": "periodic", "MetricReportDefinitionType": "Periodic"},
        "/custom/member/report": {"@odata.id": "/custom/member/report", "Id": "latest", "MetricValues": [{"MetricId": "temperature", "MetricValue": "42", "Timestamp": "2026-09-29T00:00:00Z"}]},
        "/custom/member/trigger": {"@odata.id": "/custom/member/trigger", "Id": "hot", "TriggerActions": ["LogToLogService"]},
        "/custom/log": {"@odata.id": "/custom/log", "Entries": {"@odata.id": "/custom/entries"}},
        "/custom/entry": {"@odata.id": "/custom/entry", "Id": "entry", "Message": "Threshold exceeded"},
    }
    collections = {
        "/custom/definitions": "/custom/member/definition",
        "/custom/report-definitions": "/custom/member/report-definition",
        "/custom/reports": "/custom/member/report",
        "/custom/triggers": "/custom/member/trigger",
        "/custom/entries": "/custom/entry",
    }
    monkeypatch.setattr(client, "_get_root", lambda: root)
    monkeypatch.setattr(client._http_client, "get", lambda path, model: model.model_validate(resources[path]))
    monkeypatch.setattr(client._http_client, "get_raw", lambda path: {"Members": [{"@odata.id": collections[path]}]})
    yield client
    client.close()


@pytest.mark.parametrize("plural,singular,identifier", [
    ("get_metric_definitions", "get_metric_definition", "temperature"),
    ("get_metric_report_definitions", "get_metric_report_definition", "periodic"),
    ("get_metric_reports", "get_metric_report", "latest"),
    ("get_telemetry_triggers", "get_telemetry_trigger", "hot"),
])
def test_collections_and_members_follow_links(telemetry_client, plural, singular, identifier):
    members = getattr(telemetry_client, plural)()
    assert len(members) == 1
    assert getattr(telemetry_client, singular)(identifier).id == identifier
    assert getattr(telemetry_client, singular)(members[0].odata_id).id == identifier
    with pytest.raises(RedfishNotFoundError):
        getattr(telemetry_client, singular)("missing")


def test_service_and_metric_report_log(telemetry_client):
    assert telemetry_client.get_telemetry_service().service_enabled is True
    assert telemetry_client.get_metric_report_log().odata_id == "/custom/log"
    assert telemetry_client.get_metric_report_log_entries()[0].message == "Threshold exceeded"
    assert telemetry_client.get_metric_reports()[0].metric_values[0].metric_value == "42"


@pytest.mark.parametrize("payload", [{}, {"TelemetryService": {}}, {"TelemetryService": {"@odata.id": ""}}])
def test_absent_root_capability_fails_clearly(monkeypatch, payload):
    client = RedfishClient(host="mock-bmc", username="user", password="password")
    monkeypatch.setattr(client, "_get_root", lambda: RootService.model_validate(payload))
    with pytest.raises(RedfishNotFoundError, match="TelemetryService"):
        client.get_telemetry_service()
    client.close()


def test_absent_collection_and_ambiguous_member(telemetry_client, monkeypatch):
    service = telemetry_client.get_telemetry_service()
    service.triggers = None
    monkeypatch.setattr(telemetry_client._telemetry, "get", lambda: service)
    with pytest.raises(RedfishNotFoundError, match="Triggers"):
        telemetry_client.get_telemetry_triggers()
    member = MetricReport.model_validate({"Id": "duplicate", "@odata.id": "/custom/one"})
    monkeypatch.setattr(telemetry_client._telemetry, "reports", lambda: [member, member])
    with pytest.raises(RedfishValidationError, match="Multiple"):
        telemetry_client.get_metric_report("duplicate")


def test_metric_report_definition_preserves_core_fields():
    definition = MetricReportDefinition.model_validate({
        "Metrics": [{"MetricId": "temperature", "MetricProperties": ["/custom/sensor#/Reading"], "CollectionFunction": "Average"}],
        "Schedule": {"RecurrenceInterval": "PT1M"},
        "ReportActions": ["RedfishEvent"], "Oem": {"AMI": {"Enabled": True}},
    })
    assert definition.metrics[0].collection_function == "Average"
    assert definition.schedule.recurrence_interval == "PT1M"
    assert definition.oem["AMI"]["Enabled"] is True
