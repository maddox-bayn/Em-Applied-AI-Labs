"""Chapter 11. locust -f loadfile.py --host http://localhost:8080"""
from locust import HttpUser, between, task


class Reader(HttpUser):
    wait_time = between(.2,1)

    @task(4)
    def short(self) -> None:
        self.client.post("/generate",json={"prompt":"Summarize a rejected invoice."},name="short")

    @task(1)
    def long(self) -> None:
        self.client.post("/generate",json={"prompt":"Review this invoice. " * 150},name="long")
