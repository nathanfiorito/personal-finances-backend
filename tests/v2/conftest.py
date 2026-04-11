import pytest


# Enable asyncio for all tests under tests/v2/ without needing
# @pytest.mark.asyncio on every function.
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
