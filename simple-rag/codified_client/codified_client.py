import contextvars
import requests

from contextlib import contextmanager
from requests.exceptions import HTTPError
from typing import Iterator, TypedDict

__all__ = ["AccessContext", "CodifiedClient", "access_context", "get_access_context"]

class AccessContext(TypedDict):
    user_email: str

class Holder:
    def __init__(self, ctx: AccessContext | None = None):
        self.ctx = ctx

runtime_context = contextvars.ContextVar("access_check_params", default=Holder())

@contextmanager
def access_context(user_email: str) -> Iterator[None]:
    token = runtime_context.set(Holder(AccessContext(user_email=user_email)))
    try:
        yield
    finally:
        runtime_context.reset(token)

def get_access_context() -> AccessContext | None:
    return runtime_context.get().ctx


class CodifiedClient:
    def __init__(self, api_key: str, endpoint_url: str) -> None:
        self.api_key = api_key
        self.endpoint_url = endpoint_url

    def check_access(self, data_ids: list[str], user_email: str) -> dict[str, bool]:
        response = requests.post(
            url=f"{self.endpoint_url}/api/v1/access/check",
            json={
                "data": [{"id": data_id} for data_id in data_ids],
                "username": user_email,
            },
            headers={"x-codified-api-key": self.api_key}
        )

        if response.status_code != requests.codes["ok"]:
            raise HTTPError(response=response)
        
        data = response.json()
        if not "results" in data:
            raise RuntimeError()
        
        results: dict[str, bool] = {r["data"]["id"]: r["has_permission"] for r in data["results"]}
        return results
