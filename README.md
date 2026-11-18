# The Em Applied AI Engineering · lab companion

From the extracted directory, on Linux Mint:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install numpy scikit-learn 'pydantic>=2,<3'
python ch02.py starter
python ch02.py solution
python audit.py
```

Run any numbered lab with the starter or solution argument. The default is solution. For Chapter 1, use the extracted chapter01 files and the commands in the manuscript. Its standalone lab also runs with the standard library. In Chapter 2, the fixture's calendar and thread IDs are deliberately simple; replace them with immutable metadata for a real event warehouse.

| Chapter | Additional installation or command |
|---|---|
| 2 · API | Install fastapi and uvicorn. Run uvicorn route_api:app and POST invoice_id and reason as JSON to /route. Use a different port from Chapter 1. |
| 3 · Decoder | Install torch. Run python ch03.py starter and python ch03.py solution. No weights or GPU required. |
| 4 · Live extraction | Install openai. Set OPENAI_API_KEY and VISION_MODEL to an accessible vision-capable chat model. Run python live_extract.py receipt.png. This sends the image to the provider. The offline fixture needs no key. |
| 5–6 · Hybrid search | Install qdrant-client rank-bm25 sentence-transformers. Run python hybrid_index.py. Model downloads require network access. |
| 7 · Hugging Face adapter | Install torch transformers peft sentencepiece. Run python hf_adapter.py ./invoice-adapter. Downloads a base model. The NumPy recovery lab uses no weights or GPU. |
| 8 · Workflow | Install langgraph. Run python workflow.py. The state-machine extension demonstrates the approval branch. The numbered lab persists action state. |
| 9 · Release gate | python ch09.py solution --gate deliberately exits 1. A release pipeline must interpret this as a block. |
| 10 · Tracing | Install opentelemetry-sdk. Run python observe.py and inspect the shared trace ID. |
| 11 · Gateway | Install fastapi uvicorn httpx locust. Set SERVED_MODEL to a model exposed by your inference service and INFERENCE_URL to its origin. Start uvicorn serve:app --port 8080. The gateway expects /health and /v1/completions. For a supported GPU with vLLM installed, launch vllm serve YOUR_MODEL on port 8000. |
| 11 · Load test | locust -f loadfile.py --host http://localhost:8080 --headless -u 10 -r 2 -t 60s. Repeat with 1 and 100 users. Record the hardware, model revision, token lengths, concurrency, failures and p95. |

**Verification scope.** The local exercises for Chapters 2 and 4–11 were executed in starter and solution modes. The Chapter 1 SQLite lab was executed. The source was syntax-checked. The optional integrations, PyTorch decoder and Docker/PostgreSQL integration need a suitable environment for runtime verification. Simulated latencies in Chapters 10–11 are exercise inputs. Never use synthetic results as production capacity estimates.
