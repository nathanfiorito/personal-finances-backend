from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

try:
    from opentelemetry import trace as _trace
    from opentelemetry.trace import StatusCode
    _HAS_OTEL = True
    STATUS_ERROR = StatusCode.ERROR
except ImportError:
    _HAS_OTEL = False
    STATUS_ERROR = "ERROR"  # sentinel passed to _NoopSpan.set_status — value is ignored


class _NoopSpan:
    """Drop-in for an OTel span when tracing is unavailable or not configured."""

    def set_attribute(self, key: str, value: object) -> None:
        pass

    def set_status(self, status: object, description: str = "") -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass


@contextmanager
def start_span(name: str, attributes: dict | None = None) -> Iterator[_NoopSpan | Any]:
    """
    Context manager that creates a child OTel span when tracing is configured,
    or yields a _NoopSpan otherwise. Always safe to call span.set_attribute() etc.

    get_tracer() is called lazily here (not at import time) so the global provider
    set up in main.py is always already initialized before any span is created.
    """
    if not _HAS_OTEL:
        yield _NoopSpan()
        return
    tracer = _trace.get_tracer("personal-finances")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span
