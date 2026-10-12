"""CompositionService, ResourceBlock, and ResourceZone (DMTF Zone) models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import Entity, Link, Status


class CompositionResource(Entity):
    actions: Optional[Dict[str, Any]] = Field(None, alias="Actions")
    oem: Optional[Dict[str, Any]] = Field(None, alias="Oem")
    status: Optional[Status] = Field(None, alias="Status")


class CompositionService(CompositionResource):
    service_enabled: Optional[bool] = Field(None, alias="ServiceEnabled")
    allow_overprovisioning: Optional[bool] = Field(None, alias="AllowOverprovisioning")
    allow_zone_affinity: Optional[bool] = Field(None, alias="AllowZoneAffinity")
    resource_blocks: Optional[Link] = Field(None, alias="ResourceBlocks")
    resource_zones: Optional[Link] = Field(None, alias="ResourceZones")
    active_pool: Optional[Link] = Field(None, alias="ActivePool")
    free_pool: Optional[Link] = Field(None, alias="FreePool")
    composition_reservations: Optional[Link] = Field(None, alias="CompositionReservations")
    reservation_duration: Optional[str] = Field(None, alias="ReservationDuration")


class CompositionStatus(Entity):
    composition_state: Optional[str] = Field(None, alias="CompositionState")
    max_compositions: Optional[int] = Field(None, alias="MaxCompositions")
    number_of_compositions: Optional[int] = Field(None, alias="NumberOfCompositions")
    reserved: Optional[bool] = Field(None, alias="Reserved")
    sharing_capable: Optional[bool] = Field(None, alias="SharingCapable")
    sharing_enabled: Optional[bool] = Field(None, alias="SharingEnabled")


class ResourceBlockLinks(Entity):
    chassis: Optional[List[Link]] = Field(None, alias="Chassis")
    computer_systems: Optional[List[Link]] = Field(None, alias="ComputerSystems")
    zones: Optional[List[Link]] = Field(None, alias="Zones")
    oem: Optional[Dict[str, Any]] = Field(None, alias="Oem")


class ResourceBlock(CompositionResource):
    resource_block_type: Optional[List[str]] = Field(None, alias="ResourceBlockType")
    composition_status: Optional[CompositionStatus] = Field(None, alias="CompositionStatus")
    computer_systems: Optional[List[Link]] = Field(None, alias="ComputerSystems")
    drives: Optional[List[Link]] = Field(None, alias="Drives")
    ethernet_interfaces: Optional[List[Link]] = Field(None, alias="EthernetInterfaces")
    memory: Optional[List[Link]] = Field(None, alias="Memory")
    network_interfaces: Optional[List[Link]] = Field(None, alias="NetworkInterfaces")
    processors: Optional[List[Link]] = Field(None, alias="Processors")
    simple_storage: Optional[List[Link]] = Field(None, alias="SimpleStorage")
    storage: Optional[List[Link]] = Field(None, alias="Storage")
    links: Optional[ResourceBlockLinks] = Field(None, alias="Links")


class ResourceZoneLinks(Entity):
    resource_blocks: Optional[List[Link]] = Field(None, alias="ResourceBlocks")
    endpoints: Optional[List[Link]] = Field(None, alias="Endpoints")
    contains_zones: Optional[List[Link]] = Field(None, alias="ContainsZones")
    contained_by_zones: Optional[List[Link]] = Field(None, alias="ContainedByZones")
    involved_switches: Optional[List[Link]] = Field(None, alias="InvolvedSwitches")
    address_pools: Optional[List[Link]] = Field(None, alias="AddressPools")
    oem: Optional[Dict[str, Any]] = Field(None, alias="Oem")


class ResourceZone(CompositionResource):
    """A Zone resource advertised by CompositionService.ResourceZones."""

    zone_type: Optional[str] = Field(None, alias="ZoneType")
    default_routing_enabled: Optional[bool] = Field(None, alias="DefaultRoutingEnabled")
    external_accessibility: Optional[str] = Field(None, alias="ExternalAccessibility")
    identifiers: Optional[List[Dict[str, Any]]] = Field(None, alias="Identifiers")
    links: Optional[ResourceZoneLinks] = Field(None, alias="Links")
