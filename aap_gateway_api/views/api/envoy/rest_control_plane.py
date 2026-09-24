import logging

from django.core.cache import cache
from django.db.models import Prefetch
from envoy.config.cluster.v3.cluster_pb2 import Cluster
from envoy.config.listener.v3.listener_pb2 import Listener
from envoy.service.discovery.v3.discovery_pb2 import DiscoveryResponse
from google.protobuf import symbol_database
from google.protobuf.any_pb2 import Any
from google.protobuf.json_format import MessageToDict, ParseDict
from rest_framework.response import Response
from rest_framework.views import APIView

from aap_gateway_api.models import HTTPPort, Route
from aap_gateway_api.models.service_cluster import ServiceCluster
from aap_gateway_api.models.service_type import DefaultServiceType

# these have to be imported even though they aren't used so that they get registered
# with symbol_database.Default().pool
# isort: off
from envoy.extensions.transport_sockets.tls.v3 import tls_pb2  # noqa: F401
from envoy.extensions.filters.http.router.v3 import router_pb2  # noqa: F401
from envoy.extensions.filters.http.lua.v3 import lua_pb2  # noqa: F401
from envoy.extensions.access_loggers.stream.v3 import stream_pb2  # noqa: F401
from envoy.extensions.filters.http.ext_authz.v3 import ext_authz_pb2  # noqa: F401
from envoy.extensions.filters.network.http_connection_manager.v3 import http_connection_manager_pb2  # noqa: F401
from envoy.service.secret.v3 import sds_pb2, sds_pb2_grpc  # noqa: F401
from envoy.extensions.transport_sockets.tls.v3.secret_pb2 import Secret
from aap_gateway_api.models.ca_certificate import CACertificate
from aap_gateway_api.utils.xds_configs import SDS_SECRET_CONFIG_NAME
from drf_spectacular.utils import extend_schema

# isort: on

logger = logging.getLogger("aap_gateway_api.views.api.envoy.rest_control_plane")

XDS_CACHE_KEY_CDS = "xds:cds"
XDS_CACHE_KEY_LDS = "xds:lds"
XDS_CACHE_KEY_SDS = "xds:sds"

# ---------------------------------------------------------------------------
# Envoy xDS REST control plane views
#
# These views implement the Envoy REST-JSON variant of the xDS discovery
# protocol.  Envoy POSTs a DiscoveryRequest and expects a DiscoveryResponse
# back.  There are three resource types served here:
#
#   CDS (Cluster Discovery Service)  - upstream cluster definitions
#   LDS (Listener Discovery Service) - listener + filter-chain definitions
#   SDS (Secret Discovery Service)   - TLS certificates / CA bundles
#
# None of these endpoints require authentication because they are only
# reachable from Envoy on the loopback interface.
#
# Responses are cached and invalidated by model signals (see
# aap_gateway_api/signals/xds_cache.py) so that the ~5-second Envoy
# polling interval does not trigger full DB rebuilds every time.
# ---------------------------------------------------------------------------


def invalidate_xds_cache(*keys):
    """Delete one or more xDS cache keys."""
    cache.delete_many(keys)


@extend_schema(exclude=True)
class XDSView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_qs(self, request, model_class, name_field):
        # This line (DISTINCT ON) is PostgreSQL-specific
        qs = model_class.objects.order_by(name_field).distinct(name_field)

        if names := request.POST.get("resource_names"):
            if len(names) == 1 and names[0] == "*":
                return qs
            qs = qs.filter(**{f"{name_field}__in": names})

        return qs

    def get_xds_response(self, resource_type, resources):
        response = DiscoveryResponse()
        for resource in resources:
            # load the Cluster object from our config dict
            c = resource_type()
            ParseDict(resource, c, descriptor_pool=symbol_database.Default().pool)

            # convert the Cluster message to Any
            a = Any()
            a.Pack(c)

            response.resources.append(a)

        return MessageToDict(response)


class ClusterDiscoverServiceView(XDSView):
    def post(self, request, format=None):
        cached = cache.get(XDS_CACHE_KEY_CDS)
        if cached is not None:
            logger.debug("CDS cache hit")
            return Response(cached)

        routes = list(
            self.get_qs(request, Route, "envoy_cluster_name")
            .select_related('service_cluster')
            .prefetch_related('service_cluster__nodes', 'service_cluster__service_type')
        )

        clusters = [x.get_xds_cluster_config() for x in routes]
        response_data = self.get_xds_response(Cluster, clusters)
        # Only cache if we have resources; empty responses during bootstrap should not be cached
        if clusters:
            cache.set(XDS_CACHE_KEY_CDS, response_data)
        return Response(response_data)


class ListenerDiscoverServiceView(XDSView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, format=None):
        cached = cache.get(XDS_CACHE_KEY_LDS)
        if cached is not None:
            return Response(cached)

        ports = self.get_qs(request, HTTPPort, "envoy_listener_name").prefetch_related(
            Prefetch('routes', queryset=Route.objects.select_related('service_cluster__service_type').order_by('order')),
            'routes__service_cluster__nodes',
        )

        gw_cluster_name = None
        sc = ServiceCluster.objects.filter(service_type__name=DefaultServiceType.GATEWAY.value).first()
        if sc:
            gw_route = Route.objects.filter(service_cluster=sc).first()
            if gw_route:
                gw_cluster_name = gw_route.envoy_cluster_name

        listeners = [x.get_xds_listener_config(gateway_cluster_name=gw_cluster_name) for x in ports]

        response_data = self.get_xds_response(Listener, listeners)
        # Only cache if we have resources; empty responses during bootstrap should not be cached
        if listeners:
            cache.set(XDS_CACHE_KEY_LDS, response_data)
        return Response(response_data)


class SecretDiscoverServiceView(XDSView):
    # SDS endpoint has no authentication (by design for internal Envoy access)
    authentication_classes = []
    permission_classes = []

    def post(self, request, format=None):
        cached = cache.get(XDS_CACHE_KEY_SDS)
        if cached is not None:
            return Response(cached)

        secret_resource = self._collect_db_ca_certs()
        response_data = self.get_xds_response(Secret, [secret_resource])
        cache.set(XDS_CACHE_KEY_SDS, response_data)
        return Response(response_data)

    def _collect_db_ca_certs(self) -> dict:
        certs = [cert.pem_data for cert in CACertificate.objects.all()]
        cert_data = "\n".join(certs)

        return {"name": SDS_SECRET_CONFIG_NAME, "validation_context": {"trusted_ca": {"inline_string": cert_data}}}
