import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import httpx
import psycopg

URL = "http://127.0.0.1:8000/events"


def test_overlapping_deliveries() -> None:
    key = str(uuid4())
    body = {"invoice_id": "INV-42", "reason": "currency mismatch"}
    headers = {"Idempotency-Key": key}
    gate = Barrier(20)

    with httpx.Client(timeout=15) as client:
        def deliver(_: int) -> httpx.Response:
            gate.wait(timeout=10)
            return client.post(URL, headers=headers, json=body)

        with ThreadPoolExecutor(max_workers=20) as pool:
            replies = list(pool.map(deliver, range(20)))
        assert sorted(r.status_code for r in replies) == [200] * 19 + [201]
        ids = {r.json()["event_id"] for r in replies}
        assert len(ids) == 1
        changed = client.post(URL, headers=headers, json={**body, "reason": "changed"})
        assert changed.status_code == 409

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        counts = conn.execute(
            """SELECT count(*), count(j.event_id) FROM events e
               LEFT JOIN jobs j ON j.event_id=e.id AND j.state='pending'
               WHERE e.tenant=%s AND e.delivery_key=%s""",
            (os.environ["TENANT"], key),
        ).fetchone()
        assert counts == (1, 1)
