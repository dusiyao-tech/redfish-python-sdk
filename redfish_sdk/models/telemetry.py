"""Typed Redfish telemetry resources; unrecognized vendor fields are preserved."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import Entity, Link, Status


class TelemetryResource(Entity):
    actions: Optional[Dict[str, Any]] = Field(None, alias="Actions")
    oem: Optional[Dict[str, Any]] = Field(None, alias="Oem")
    status: Optional[Status] = Field(None, alias="Status")


class TelemetryService(TelemetryResource):
    service_enabled: Optional[bool] = Field(None, alias="ServiceEnabled")
    max_reports: Optional[int] = Field(None, alias="MaxReports")
    min_collection_interval: Optional[str] = Field(None, alias="MinCollectionInterval")
    supported_collection_functions: Optional[List[str]] = Field(None, alias="SupportedCollectionFunctions")
    metric_definitions: Optional[Link] = Field(None, alias="MetricDefinitions")
    metric_report_definitions: Optional[Link] = Field(None, alias="MetricReportDefinitions")
    metric_reports: Optional[Link] = Field(None, alias="MetricReports")
    triggers: Optional[Link] = Field(None, alias="Triggers")
    log_service: Optional[Link] = Field(None, alias="LogService")
    metric_report_log: Optional[Link] = Field(None, alias="MetricReportLog")


class MetricWildcard(Entity):
    values: Optional[List[str]] = Field(None, alias="Values")
    keys: Optional[List[str]] = Field(None, alias="Keys")


class MetricDefinition(TelemetryResource):
    metric_type: Optional[str] = Field(None, alias="MetricType")
    metric_data_type: Optional[str] = Field(None, alias="MetricDataType")
    metric_properties: Optional[List[str]] = Field(None, alias="MetricProperties")
    units: Optional[str] = Field(None, alias="Units")
    physical_context: Optional[str] = Field(None, alias="PhysicalContext")
    calculable: Optional[str] = Field(None, alias="Calculable")
    implementation: Optional[str] = Field(None, alias="Implementation")
    precision: Optional[int] = Field(None, alias="Precision")
    accuracy: Optional[float] = Field(None, alias="Accuracy")
    calibration: Optional[float] = Field(None, alias="Calibration")
    min_reading_range: Optional[float] = Field(None, alias="MinReadingRange")
    max_reading_range: Optional[float] = Field(None, alias="MaxReadingRange")
    is_linear: Optional[bool] = Field(None, alias="IsLinear")
    discrete_values: Optional[List[str]] = Field(None, alias="DiscreteValues")
    sensing_interval: Optional[str] = Field(None, alias="SensingInterval")
    timestamp_accuracy: Optional[str] = Field(None, alias="TimestampAccuracy")
    calculation_algorithm: Optional[str] = Field(None, alias="CalculationAlgorithm")
    calculation_parameters: Optional[List[Dict[str, Any]]] = Field(None, alias="CalculationParameters")
    calculation_time_interval: Optional[str] = Field(None, alias="CalculationTimeInterval")
    wildcards: Optional[List[MetricWildcard]] = Field(None, alias="Wildcards")


class Metric(Entity):
    metric_id: Optional[str] = Field(None, alias="MetricId")
    metric_properties: Optional[List[str]] = Field(None, alias="MetricProperties")
    collection_duration: Optional[str] = Field(None, alias="CollectionDuration")
    collection_function: Optional[str] = Field(None, alias="CollectionFunction")
    collection_time_scope: Optional[str] = Field(None, alias="CollectionTimeScope")


class MetricSchedule(Entity):
    initial_start_time: Optional[str] = Field(None, alias="InitialStartTime")
    recurrence_interval: Optional[str] = Field(None, alias="RecurrenceInterval")
    lifetime: Optional[str] = Field(None, alias="Lifetime")
    max_occurrences: Optional[int] = Field(None, alias="MaxOccurrences")


class MetricReportDefinition(TelemetryResource):
    metric_report_definition_enabled: Optional[bool] = Field(None, alias="MetricReportDefinitionEnabled")
    metric_report_definition_type: Optional[str] = Field(None, alias="MetricReportDefinitionType")
    metric_report_heartbeat_interval: Optional[str] = Field(None, alias="MetricReportHeartbeatInterval")
    metric_report: Optional[Link] = Field(None, alias="MetricReport")
    metric_properties: Optional[List[str]] = Field(None, alias="MetricProperties")
    metrics: Optional[List[Metric]] = Field(None, alias="Metrics")
    schedule: Optional[MetricSchedule] = Field(None, alias="Schedule")
    report_actions: Optional[List[str]] = Field(None, alias="ReportActions")
    report_updates: Optional[str] = Field(None, alias="ReportUpdates")
    report_timespan: Optional[str] = Field(None, alias="ReportTimespan")
    append_limit: Optional[int] = Field(None, alias="AppendLimit")
    suppress_repeated_metric_value: Optional[bool] = Field(None, alias="SuppressRepeatedMetricValue")
    wildcards: Optional[List[MetricWildcard]] = Field(None, alias="Wildcards")
    links: Optional[Dict[str, Any]] = Field(None, alias="Links")


class MetricValue(Entity):
    metric_id: Optional[str] = Field(None, alias="MetricId")
    metric_definition: Optional[Link] = Field(None, alias="MetricDefinition")
    metric_property: Optional[str] = Field(None, alias="MetricProperty")
    metric_value: Optional[str] = Field(None, alias="MetricValue")
    timestamp: Optional[str] = Field(None, alias="Timestamp")
    oem: Optional[Dict[str, Any]] = Field(None, alias="Oem")


class MetricReport(TelemetryResource):
    metric_report_definition: Optional[Link] = Field(None, alias="MetricReportDefinition")
    metric_values: Optional[List[MetricValue]] = Field(None, alias="MetricValues")
    report_sequence: Optional[str] = Field(None, alias="ReportSequence")
    timestamp: Optional[str] = Field(None, alias="Timestamp")


class DiscreteTrigger(Entity):
    dwell_time: Optional[str] = Field(None, alias="DwellTime")
    severity: Optional[str] = Field(None, alias="Severity")
    value: Optional[str] = Field(None, alias="Value")


class MetricThreshold(Entity):
    activation: Optional[str] = Field(None, alias="Activation")
    dwell_time: Optional[str] = Field(None, alias="DwellTime")
    reading: Optional[float] = Field(None, alias="Reading")


class MetricThresholds(Entity):
    lower_critical: Optional[MetricThreshold] = Field(None, alias="LowerCritical")
    lower_warning: Optional[MetricThreshold] = Field(None, alias="LowerWarning")
    upper_critical: Optional[MetricThreshold] = Field(None, alias="UpperCritical")
    upper_warning: Optional[MetricThreshold] = Field(None, alias="UpperWarning")


class Triggers(TelemetryResource):
    metric_type: Optional[str] = Field(None, alias="MetricType")
    metric_properties: Optional[List[str]] = Field(None, alias="MetricProperties")
    trigger_actions: Optional[List[str]] = Field(None, alias="TriggerActions")
    discrete_trigger_condition: Optional[str] = Field(None, alias="DiscreteTriggerCondition")
    discrete_triggers: Optional[List[DiscreteTrigger]] = Field(None, alias="DiscreteTriggers")
    numeric_thresholds: Optional[MetricThresholds] = Field(None, alias="NumericThresholds")
    event_triggers: Optional[List[str]] = Field(None, alias="EventTriggers")
    wildcards: Optional[List[MetricWildcard]] = Field(None, alias="Wildcards")
    links: Optional[Dict[str, Any]] = Field(None, alias="Links")
