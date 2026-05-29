import pytest
from django.test import RequestFactory

from config.middleware import CanonicalHostMiddleware


@pytest.fixture
def get_response():
    def _get_response(request):
        from django.http import HttpResponse

        return HttpResponse("ok")

    return _get_response


@pytest.fixture
def middleware(get_response, settings):
    settings.CANONICAL_HOST = "canistillcode.org"
    settings.CANONICAL_REDIRECT_HOSTS = ["www.canistillcode.org"]
    settings.ALLOWED_HOSTS = ["canistillcode.org", "www.canistillcode.org"]
    return CanonicalHostMiddleware(get_response)


class TestCanonicalHostMiddleware:
    def test_www_redirects_with_301(self, middleware):
        request = RequestFactory(SERVER_NAME="www.canistillcode.org").get("/")
        response = middleware(request)
        assert response.status_code == 301

    def test_homepage_redirect_location(self, middleware):
        request = RequestFactory(SERVER_NAME="www.canistillcode.org").get("/")
        response = middleware(request)
        assert response["Location"] == "https://canistillcode.org/"

    def test_path_and_query_string_preserved(self, middleware):
        request = RequestFactory(SERVER_NAME="www.canistillcode.org").get(
            "/accounts/login/", {"next": "/dashboard/"}
        )
        response = middleware(request)
        assert response.status_code == 301
        assert response["Location"] == "https://canistillcode.org/accounts/login/?next=%2Fdashboard%2F"

    def test_canonical_host_does_not_redirect(self, middleware):
        request = RequestFactory(SERVER_NAME="canistillcode.org").get("/")
        response = middleware(request)
        assert response.status_code == 200
