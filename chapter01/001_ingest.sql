CREATE TABLE events (
    id uuid PRIMARY KEY,
    tenant text NOT NULL,
    delivery_key text NOT NULL,
    body jsonb NOT NULL,
    UNIQUE (tenant, delivery_key)
);
CREATE TABLE jobs (
    event_id uuid PRIMARY KEY REFERENCES events(id),
    state text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','running','done')),
    queued_at timestamptz NOT NULL DEFAULT now()
);
