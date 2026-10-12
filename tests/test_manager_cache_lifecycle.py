"""Manager cleanup covers optional services without editing a shared registry."""

from functools import cached_property

import pytest

from redfish_sdk import RedfishClient


class ExtendedClient(RedfishClient):
    @cached_property
    def _extra_manager(self):
        return object()


@pytest.mark.parametrize("client_class", [RedfishClient, ExtendedClient])
def test_close_clears_all_cached_managers(client_class):
    client = client_class(host="mock-bmc", username="user", password="password")
    names = {
        name for ancestor in client_class.__mro__ for name, descriptor in vars(ancestor).items()
        if isinstance(descriptor, cached_property)
    }
    for name in names:
        getattr(client, name)
    assert names.issubset(vars(client))
    client.close()
    assert names.isdisjoint(vars(client))
