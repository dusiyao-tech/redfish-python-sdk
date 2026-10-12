"""Optional CompositionService discovery and read operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Type, TypeVar

from ..exceptions import RedfishNotFoundError, RedfishValidationError
from ..models.common import Entity
from ..models.composition import CompositionService, ResourceBlock, ResourceZone

if TYPE_CHECKING:
    from ..client import RedfishClient

CompositionMember = TypeVar("CompositionMember", bound=Entity)


class CompositionServiceManager:
    def __init__(self, client: RedfishClient):
        self._client = client
        self._http = client._http_client

    def get(self) -> CompositionService:
        link = self._client._get_root().composition_service
        if not link or not link.odata_id:
            raise RedfishNotFoundError("Service Root does not advertise CompositionService")
        return self._http.get(link.odata_id, CompositionService)

    def _collection(self, field: str, model: Type[CompositionMember]) -> List[CompositionMember]:
        link = getattr(self.get(), field)
        if not link or not link.odata_id:
            alias = CompositionService.model_fields[field].alias
            raise RedfishNotFoundError(f"CompositionService does not advertise {alias}")
        return self._client._get_collection(link.odata_id, model)

    def blocks(self) -> List[ResourceBlock]:
        return self._collection("resource_blocks", ResourceBlock)

    def zones(self) -> List[ResourceZone]:
        return self._collection("resource_zones", ResourceZone)

    @staticmethod
    def member(resources: List[CompositionMember], identifier: str) -> CompositionMember:
        matches = [resource for resource in resources if resource.id == identifier or resource.odata_id == identifier]
        if not matches:
            raise RedfishNotFoundError(f"No composition member with Id or @odata.id {identifier!r}")
        if len(matches) > 1:
            raise RedfishValidationError("Multiple composition members match; specify a unique @odata.id")
        return matches[0]
