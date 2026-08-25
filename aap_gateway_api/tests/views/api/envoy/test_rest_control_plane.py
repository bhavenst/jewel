"""Unit tests for Envoy REST control plane xDS cache behavior."""

import pytest
from django.urls import reverse

from aap_gateway_api.views.api.envoy.rest_control_plane import XDS_CACHE_KEY_CDS, XDS_CACHE_KEY_LDS, XDS_CACHE_KEY_SDS


@pytest.mark.django_db
def test_cds_cache_hit_returns_cached_response(unauthenticated_api_client, full_service_hierarchy_controller):
    """Second CDS call returns cached response without hitting the DB."""
    from django.core.cache import cache

    url = reverse("cds")
    first = unauthenticated_api_client.post(url, data={})
    assert first.status_code == 200
    assert cache.get(XDS_CACHE_KEY_CDS) is not None
    second = unauthenticated_api_client.post(url, data={})
    assert second.status_code == 200
    assert second.data == first.data


@pytest.mark.django_db
def test_lds_cache_hit_returns_cached_response(unauthenticated_api_client, full_service_hierarchy_controller):
    """Second LDS call returns cached response without hitting the DB."""
    from django.core.cache import cache

    url = reverse("lds")
    first = unauthenticated_api_client.post(url, data={})
    assert first.status_code == 200
    assert cache.get(XDS_CACHE_KEY_LDS) is not None
    second = unauthenticated_api_client.post(url, data={})
    assert second.status_code == 200
    assert second.data == first.data


@pytest.mark.django_db
def test_sds_cache_hit_returns_cached_response(unauthenticated_api_client):
    """Second SDS call returns cached response."""
    from django.core.cache import cache

    url = reverse("sds")
    first = unauthenticated_api_client.post(url, data={})
    assert first.status_code == 200
    assert cache.get(XDS_CACHE_KEY_SDS) is not None
    second = unauthenticated_api_client.post(url, data={})
    assert second.status_code == 200
    assert second.data == first.data


@pytest.mark.django_db
def test_lds_no_gateway_cluster(unauthenticated_api_client, full_service_hierarchy_controller):
    """LDS succeeds when no GATEWAY ServiceCluster exists."""
    from aap_gateway_api.models.service_cluster import ServiceCluster
    from aap_gateway_api.models.service_type import DefaultServiceType

    ServiceCluster.objects.filter(service_type__name=DefaultServiceType.GATEWAY.value).delete()
    url = reverse("lds")
    response = unauthenticated_api_client.post(url, data={})
    assert response.status_code == 200
