import pytest
from src.services.tracing import _NoopSpan, start_span


class TestNoopSpan:
    def test_set_attribute_does_not_raise(self):
        span = _NoopSpan()
        span.set_attribute("db.rows", 5)  # must not raise

    def test_set_status_does_not_raise(self):
        span = _NoopSpan()
        span.set_status("ERROR", "something failed")  # must not raise

    def test_record_exception_does_not_raise(self):
        span = _NoopSpan()
        span.record_exception(ValueError("oops"))  # must not raise


class TestStartSpan:
    def test_yields_object_with_set_attribute(self):
        with start_span("test.op") as span:
            assert hasattr(span, "set_attribute")

    def test_yields_object_with_set_status(self):
        with start_span("test.op") as span:
            assert hasattr(span, "set_status")

    def test_yields_object_with_record_exception(self):
        with start_span("test.op") as span:
            assert hasattr(span, "record_exception")

    def test_with_attributes_does_not_raise(self):
        with start_span("test.op", {"db.table": "transactions", "db.operation": "select"}) as span:
            span.set_attribute("db.rows", 3)  # must not raise

    def test_set_attribute_on_yielded_span_does_not_raise(self):
        with start_span("test.op") as span:
            span.set_attribute("llm.tokens_in", 42)  # must not raise

    def test_exception_propagates_through_span(self):
        with pytest.raises(ValueError, match="test error"):
            with start_span("test.op"):
                raise ValueError("test error")

    def test_start_span_yields_noop_span_when_otel_absent(self, monkeypatch):
        import src.services.tracing as tracing_module
        monkeypatch.setattr(tracing_module, "_HAS_OTEL", False)
        with tracing_module.start_span("test.op") as span:
            assert isinstance(span, tracing_module._NoopSpan)

    def test_status_error_is_otel_status_code(self):
        from opentelemetry.trace import StatusCode
        from src.services.tracing import STATUS_ERROR
        assert STATUS_ERROR is StatusCode.ERROR
