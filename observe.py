"""Chapter 10. python observe.py. Requires opentelemetry-sdk."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from ch06 import answer


def run() -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("em-support")
    with tracer.start_as_current_span("invoice.resolve") as parent:
        parent.set_attribute("release","fixture-v1")
        with tracer.start_as_current_span("policy.retrieve") as child:
            _, ids = answer("INV-042",True)
            child.set_attribute("candidates",len(ids))
            child.set_attribute("retrieval.version","hybrid-v1")
    provider.shutdown()

if __name__ == "__main__":
    run()
