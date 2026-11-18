curl -i http://localhost:8000/events \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: evt-42' \
  -d '{"invoice_id":"INV-42","reason":"currency mismatch"}'
