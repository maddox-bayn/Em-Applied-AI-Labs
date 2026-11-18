import os
from typing import Annotated
from uuid import UUID, uuid4

import psycopg
from fastapi import FastAPI, Header, HTTPException, Response
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()
DATABASE_URL = os.environ["DATABASE_URL"]
TENANT = os.environ["TENANT"]


class InvoiceRejected(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    invoice_id: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=1000)


class Receipt(BaseModel):
    event_id: UUID


@app.post("/events", response_model=Receipt, status_code=201)
def accept(
    event: InvoiceRejected,
    response: Response,
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
) -> Receipt:
    body = event.model_dump()
    proposed_id = uuid4()
    try:
        # Connection context commits on successful exit and rolls back on error.
        with psycopg.connect(DATABASE_URL, connect_timeout=3,
                             options="-c statement_timeout=3000") as conn:
            row = conn.execute(
                """INSERT INTO events (id, tenant, delivery_key, body)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (tenant, delivery_key) DO NOTHING RETURNING id""",
                (proposed_id, TENANT, idempotency_key, Jsonb(body)),
            ).fetchone()
            if row is not None:
                conn.execute("INSERT INTO jobs (event_id) VALUES (%s)", (proposed_id,))
                receipt = Receipt(event_id=proposed_id)
            else:
                # At READ COMMITTED this new statement sees the winning commit.
                prior = conn.execute(
                    "SELECT id, body FROM events WHERE tenant=%s AND delivery_key=%s",
                    (TENANT, idempotency_key),
                ).fetchone()
                if prior is None:
                    raise HTTPException(503, "Replay record unavailable")
                if prior[1] != body:
                    raise HTTPException(409, "Key already used for different content")
                receipt = Receipt(event_id=prior[0])
                response.status_code = 200
    except (psycopg.OperationalError, psycopg.errors.QueryCanceled) as exc:
        raise HTTPException(503, "Retry with the same key") from exc
    return receipt
