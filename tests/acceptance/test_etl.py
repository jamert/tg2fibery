import json
import random
import string
import subprocess
from contextlib import contextmanager
from pprint import pprint
from tempfile import NamedTemporaryFile
from typing import Optional, Union

import requests

mountebank_address = "http://mountebank:2525"


def stub(
    response: Union[dict, list, None] = None, status_code: int = 200, **predicates: dict
) -> dict:
    return {
        "responses": [
            {
                "is": {"statusCode": status_code} | {"body": response}
                if response is not None
                else {}
            }
        ],
        "predicates": [{k: pred} for k, pred in predicates.items()],
    }


@contextmanager
def telegram(message: str) -> "MockTelegram":
    tg = MockTelegram(message=message)
    try:
        tg.setup()
        yield tg
    finally:
        tg.teardown()


class MockTelegram:
    def __init__(self, message: str) -> None:
        self.port = 9090
        self._message = message
        self.token = self._random_token()
        self.address = f"{mountebank_address}".replace("2525", str(self.port))

    @staticmethod
    def _random_token() -> str:
        numbers = "".join(str(random.randint(0, 9)) for _ in range(6))
        p1 = "".join(random.choice(string.ascii_letters) for _ in range(3))
        p2 = "".join(random.choice(string.ascii_letters) for _ in range(11))
        p3 = "".join(random.choice(string.ascii_letters) for _ in range(17))
        return f"{numbers}:{p1}-{p2}-{p3}"

    def setup(self) -> None:
        requests.post(
            url=f"{mountebank_address}/imposters",
            json={
                "port": self.port,
                "protocol": "http",
                "name": "Telegram Mock",
                "recordRequests": True,
                "defaultResponse": {"statusCode": 400, "body": "Bad Request"},
                "stubs": [
                    stub(
                        equals={
                            "method": "GET",
                            "path": f"/bot{self.token}/getUpdates",
                            "query": {"limit": 1},
                        },
                        response={"result": [self.update(self._message)]},
                    )
                ],
            },
        )

    def teardown(self) -> None:
        url = f"{mountebank_address}/imposters/{self.port}"
        print(f"HARNESS:{self.__class__.__name__}", end=" ")
        pprint(requests.get(url=url).json()["requests"])
        requests.delete(url=url)

    @staticmethod
    def update(text: str) -> dict:
        return {
            "update_id": 145,
            "message": {
                "message_id": 5554,
                "text": text,
            },
        }


@contextmanager
def fibery() -> "MockFibery":
    fbr = MockFibery()
    try:
        fbr.setup()
        yield fbr
    finally:
        fbr.teardown()


class MockFibery:
    def __init__(self):
        self.port = 7070
        self.token = "4748asad.FAGA89002AJFDAFasfucuciocgah2222"
        self.address = f"{mountebank_address}".replace("2525", str(self.port))

        self.material_id = "90c6d940-ce27-11ec-b591-698a572b9bd4"
        self.material_praise_update_secret = "b33a25d1-99ba-11e9-8c59-09d0cb6f3aeb"

    def setup(self) -> None:
        requests.post(
            url=f"{mountebank_address}/imposters",
            json={
                "port": self.port,
                "protocol": "http",
                "recordRequests": True,
                "name": "Fibery Mock",
                "defaultResponse": {"statusCode": 400, "body": "Bad Request"},
                "stubs": [
                    self.create_material(),
                    self.get_material_praise_secret(),
                    self.update_material_praise(),
                ],
            },
        )

    def create_material(self) -> dict:
        return stub(
            equals={
                "method": "POST",
                "path": "/api/commands",
                "headers": {
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/json",
                },
                "body": [
                    {
                        "command": "fibery.entity/create",
                        "args": {"type": "Knowledge Management/Material"},
                    }
                ],
            },
            exists={"body": [{"args": {"entity": {"fibery/id": True}}}]},
            response=[
                {
                    "success": True,
                    "result": {
                        "fibery/id": self.material_id,
                        "Knowledge Management/Praise": {
                            "fibery/id": "e034f1c7-a069-4bb9-b606-c2545116e305"
                        },
                    },
                }
            ],
        )

    def get_material_praise_secret(self) -> dict:
        return stub(
            equals={
                "method": "POST",
                "path": "/api/commands",
                "headers": {
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/json",
                },
                "body": [
                    {
                        "command": "fibery.entity/query",
                        "args": {
                            "query": {
                                "q/from": "Knowledge Management/Material",
                                "q/select": [
                                    "fibery/id",
                                    {
                                        "Knowledge Management/Praise": [
                                            "Collaboration~Documents/secret"
                                        ]
                                    },
                                ],
                                "q/where": ["=", ["fibery/id"], "$id"],
                                "q/limit": 1,
                            },
                            "params": {"$id": self.material_id},
                        },
                    }
                ],
            },
            response=[
                {
                    "success": True,
                    "result": [
                        {
                            "fibery/id": self.material_id,
                            "Knowledge Management/Praise": {
                                "Collaboration~Documents/secret": self.material_praise_update_secret
                            },
                        }
                    ],
                }
            ],
        )

    def update_material_praise(self) -> dict:
        return stub(
            equals={
                "method": "PUT",
                "path": f"/api/documents/{self.material_praise_update_secret}",
                "query": {"format": "md"},
                "headers": {
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/json",
                },
            },
            exists={
                "body": {"content": True},
            },
        )

    def teardown(self) -> None:
        url = f"{mountebank_address}/imposters/{self.port}"
        print(f"HARNESS:{self.__class__.__name__}", end=" ")
        pprint(requests.get(url=url).json()["requests"])
        requests.delete(url=url)

    def compare_content(self, content: str) -> bool:
        response = requests.get(url=f"{mountebank_address}/imposters/{self.port}")
        return any(
            content == self._maybe_extract_content(request.get("body", ""))
            for request in response.json()["requests"]
        )

    @staticmethod
    def _maybe_extract_content(body) -> Optional[str]:
        try:
            return json.loads(body)["content"]
        except (ValueError, KeyError, TypeError):
            return None


secrets_template = """
[telegram]
netloc=http://mountebank:{telegram_port}
token={telegram_token}

[fibery]
netloc=http://mountebank:{fibery_port}
token={fibery_token}
"""


@contextmanager
def secret(tg: MockTelegram, fbr: MockFibery) -> str:
    with NamedTemporaryFile(mode="w+t", encoding="utf-8") as fd:
        fd.write(
            secrets_template.format(
                telegram_port=tg.port,
                telegram_token=tg.token,
                fibery_port=fbr.port,
                fibery_token=fbr.token,
            )
        )
        fd.flush()

        yield fd.name


def test_etl():
    text = "autogenerated"

    with telegram(message=text) as tg, fibery() as fbr:
        with secret(tg, fbr) as cfg:
            subprocess.run(["tg2fibery", "--secret", cfg])

        assert fbr.compare_content(text)
