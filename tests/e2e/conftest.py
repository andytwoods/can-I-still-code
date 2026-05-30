import pytest


@pytest.fixture(scope="session")
def base_url(request):
    """Default to localhost dev server; override with --base-url."""
    return request.config.getoption("--base-url", default=None) or "http://localhost:8000"


@pytest.fixture(scope="session")
def context(browser):
    """
    Session-scoped browser context so Pyodide's WASM is fetched once and
    cached across all challenge tests.
    """
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture
def page(context):
    """Function-scoped page within the shared context."""
    p = context.new_page()
    yield p
    p.close()
