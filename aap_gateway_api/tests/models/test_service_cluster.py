import pytest

from aap_gateway_api.models import ServiceCluster, ServiceType
from aap_gateway_api.models.service_type import DefaultServiceType


@pytest.mark.parametrize(
    "service_type,expected_path",
    [
        ('controller', '/prefix/login/'),
        ('eda', '/prefix/v1/auth/session/login/'),
        ('hub', '/auth/login'),
        ('gateway', None),
    ],
)
@pytest.mark.django_db
def test_service_cluster_login_url(service_type, expected_path):
    st = ServiceType.objects.get(name=service_type)
    sc = ServiceCluster(service_type=st)
    assert sc.get_login_path('/prefix/') == expected_path


@pytest.mark.parametrize(
    "service_type,expected_path",
    [
        ('controller', '/prefix/logout/'),
        ('eda', '/prefix/v1/auth/session/logout/'),
        ('hub', '/auth/logout'),
        ('gateway', None),
    ],
)
@pytest.mark.django_db
def test_service_cluster_logout_url(service_type, expected_path):
    st = ServiceType.objects.get(name=service_type)
    sc = ServiceCluster(service_type=st)
    assert sc.get_logout_path('/prefix/') == expected_path


@pytest.mark.parametrize("service_type,name", [('controller', 'controller'), ('hub', 'hub'), ('eda', 'eda')])
@pytest.mark.django_db
def test_get_by_type(service_type, name):
    st = ServiceType.objects.get(name=service_type)
    ServiceCluster.objects.create(name=name, service_type=st)

    sc = ServiceCluster.get_cluster_by_type(service_type=service_type)
    assert sc.name == name

    sc = ServiceCluster.get_cluster_by_type(st)
    assert sc.name == name


class TestEffectiveHealthCheckTimeout:
    @pytest.mark.parametrize(
        "health_check_timeout,preference_timeout,expected",
        [
            (5, 30, 30),
            (5, 15, 15),
            (30, 15, 30),
            (60, 30, 60),
            (5, 5, 5),
        ],
        ids=[
            "preference_higher_than_field",
            "preference_higher_than_default",
            "field_higher_than_preference",
            "field_much_higher_than_preference",
            "field_equals_preference",
        ],
    )
    @pytest.mark.django_db
    def test_effective_health_check_timeout_seconds(self, health_check_timeout, preference_timeout, expected, preference_manager):
        st = ServiceType.objects.get(name=DefaultServiceType.EDA)
        cluster = ServiceCluster.objects.create(
            name="test-effective-timeout",
            service_type=st,
            health_check_timeout_seconds=health_check_timeout,
        )
        with preference_manager.set("proxy", "request_timeout", preference_timeout):
            assert cluster.get_effective_health_check_timeout_seconds() == expected


class TestEffectiveHealthCheckInterval:
    @pytest.mark.parametrize(
        "health_check_interval,health_check_timeout,preference_timeout,expected_interval",
        [
            (10, 5, 30, 30),
            (30, 5, 30, 30),
            (60, 5, 30, 60),
            (0, 5, 30, 30),
            (10, 40, 30, 40),
        ],
        ids=[
            "interval_below_effective_timeout_uses_effective_timeout",
            "interval_equals_effective_timeout",
            "interval_above_effective_timeout_preserved",
            "zero_interval_uses_effective_timeout",
            "field_timeout_higher_than_preference_raises_floor",
        ],
    )
    @pytest.mark.django_db
    def test_effective_health_check_interval_seconds(
        self, health_check_interval, health_check_timeout, preference_timeout, expected_interval, preference_manager
    ):
        st = ServiceType.objects.get(name=DefaultServiceType.EDA)
        cluster = ServiceCluster.objects.create(
            name="test-effective-interval",
            service_type=st,
            health_check_timeout_seconds=health_check_timeout,
            health_check_interval_seconds=health_check_interval,
        )
        with preference_manager.set("proxy", "request_timeout", preference_timeout):
            assert cluster.get_effective_health_check_interval_seconds() == expected_interval
