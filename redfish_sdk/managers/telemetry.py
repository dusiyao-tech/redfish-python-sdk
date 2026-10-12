"""Discovery-based telemetry access without conventional URI assumptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Type, TypeVar

from ..exceptions import RedfishNotFoundError, RedfishValidationError
from ..models.common import Entity
from ..models.logs import Log, LogEntry
from ..models.telemetry import MetricDefinition, MetricReport, MetricReportDefinition, TelemetryService, Triggers
from ._log_helpers import fetch_log_entries

if TYPE_CHECKING:
    from ..client import RedfishClient

TelemetryMember = TypeVar("TelemetryMember", bound=Entity)


class TelemetryServiceManager:
    def __init__(self, client: RedfishClient):
        self._client = client
        self._http = client._http_client

    def get(self) -> TelemetryService:
        link = self._client._get_root().telemetry_service
        if not link or not link.odata_id:
            raise RedfishNotFoundError("Service Root does not advertise TelemetryService")
        return self._http.get(link.odata_id, TelemetryService)

    def _collection(self, field: str, model: Type[TelemetryMember]) -> List[TelemetryMember]:
        link = getattr(self.get(), field)
        if not link or not link.odata_id:
            alias = TelemetryService.model_fields[field].alias
            raise RedfishNotFoundError(f"TelemetryService does not advertise {alias}")
        return self._client._get_collection(link.odata_id, model)

    @staticmethod
    def member(resources: List[TelemetryMember], identifier: str) -> TelemetryMember:
        matches = [resource for resource in resources if resource.id == identifier or resource.odata_id == identifier]
        if not matches:
            raise RedfishNotFoundError(f"No telemetry member with Id or @odata.id {identifier!r}")
        if len(matches) > 1:
            raise RedfishValidationError("Multiple telemetry members match; specify a unique @odata.id")
        return matches[0]

    def definitions(self) -> List[MetricDefinition]:
        return self._collection("metric_definitions", MetricDefinition)

    def report_definitions(self) -> List[MetricReportDefinition]:
        return self._collection("metric_report_definitions", MetricReportDefinition)

    def reports(self) -> List[MetricReport]:
        return self._collection("metric_reports", MetricReport)

    def triggers(self) -> List[Triggers]:
        return self._collection("triggers", Triggers)

    def log(self) -> Log:
        service = self.get()
        link = service.log_service or service.metric_report_log
        if not link or not link.odata_id:
            raise RedfishNotFoundError("TelemetryService does not advertise a MetricReportLog/LogService")
        return self._http.get(link.odata_id, Log)

    def log_entries(self) -> List[LogEntry]:
        return fetch_log_entries(self._client, self.log())
