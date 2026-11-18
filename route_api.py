"""Chapter 2. uvicorn route_api:app. Uses the same event envelope as Chapter 1."""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from ch02 import fixture

app = FastAPI()
rows = [r for r in fixture()[::2] if r.day < 70]
model = make_pipeline(TfidfVectorizer(), LogisticRegression(random_state=7))
model.fit([r.reason for r in rows],[r.critical for r in rows])


class Event(BaseModel):
    invoice_id: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=1000)


@app.post("/route")
def route(event: Event) -> dict[str,str | float]:
    probability = float(model.predict_proba([event.reason])[0,1])
    return {"invoice_id":event.invoice_id,"probability":probability,
            "route":"escalate" if probability >= 0.15 else "routine"}
