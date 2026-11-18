"""Chapter 11. uvicorn serve:app --port 8080. Optional local vLLM HTTP upstream."""
import asyncio
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(base_url=os.getenv("INFERENCE_URL","http://localhost:8000"),
                                 timeout=8) as client:
        app.state.client = client
        app.state.slots = asyncio.Semaphore(8)
        yield


app = FastAPI(lifespan=lifespan)


class Request(BaseModel):
    prompt: str = Field(min_length=1,max_length=4000)


@app.get("/ready")
async def ready() -> dict[str,bool]:
    try:
        result = await app.state.client.get("/health",timeout=1)
        result.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(503,"inference unavailable") from exc
    return {"ready":True}


@app.post("/generate")
async def generate(body: Request) -> dict[str,str]:
    try:
        await asyncio.wait_for(app.state.slots.acquire(),timeout=.15)
    except TimeoutError as exc:
        raise HTTPException(503,"queue full") from exc
    try:
        async with asyncio.timeout(8):
            result = await app.state.client.post("/v1/completions",json={
                "model":os.environ["SERVED_MODEL"],"prompt":body.prompt,"max_tokens":64})
            result.raise_for_status()
            return {"text":result.json()["choices"][0]["text"]}
    except (TimeoutError,httpx.TimeoutException) as exc:
        raise HTTPException(504,"inference deadline") from exc
    except (httpx.HTTPError,KeyError,ValueError,IndexError) as exc:
        raise HTTPException(502,"invalid inference response") from exc
    finally:
        app.state.slots.release()
