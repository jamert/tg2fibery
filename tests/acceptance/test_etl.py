import random
import string
from contextlib import contextmanager

import requests

mountebank_address = "http://mountebank:2525"


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
        self._port = 9090
        self._message = message
        self.token = self._random_token()
        self.address = f"{mountebank_address}".replace("2525", str(self._port))

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
                "port": self._port,
                "protocol": "http",
                "name": "Telegram Mock",
                "defaultResponse": {"statusCode": 400, "body": "Bad Request"},
                "stubs": [
                    {
                        "responses": [
                            {
                                "is": {
                                    "statusCode": 200,
                                    "body": self.update(self._message),
                                }
                            }
                        ],
                        "predicates": [
                            {
                                "equals": {
                                    "method": "GET",
                                    "path": f"/bot{self.token}/getUpdates",
                                    "query": {"limit": 1},
                                }
                            }
                        ],
                    }
                ],
            },
        )

    def teardown(self) -> None:
        requests.delete(url=f"{mountebank_address}/imposters/{self._port}")

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
        self._port = 7070
        self.token = "Arghs"
        self.address = f"{mountebank_address}".replace("2525", str(self._port))

    def setup(self) -> None:
        requests.post(
            url=f"{mountebank_address}/imposters",
            json={
                "port": self._port,
                "protocol": "http",
                "name": "Fibery Mock",
                "defaultResponse": {"statusCode": 400, "body": "Bad Request"},
                "stubs": [self.create_material()],
            },
        )

    def create_material(self) -> dict:
        return {
            "responses": [
                {
                    "is": {
                        "statusCode": 200,
                        "body": {
                            "success": True,
                            "result": {
                                "fibery/id": "90c6d940-ce27-11ec-b591-698a572b9bd4",
                                "Knowledge Management/Praise": {
                                    "fibery/id": "e034f1c7-a069-4bb9-b606-c2545116e305"
                                },
                            },
                        },
                    }
                }
            ],
            "predicates": [
                {
                    "equals": {
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
                },
                {
                    "exists": {"body": [{"args": {"entity": {"fibery/id": True}}}]},
                },
            ],
        }

    def teardown(self) -> None:
        requests.delete(url=f"{mountebank_address}/imposters/{self._port}")


def test_etl():
    # target state:
    #   setup Telegram mock
    #   setup Fibery mock
    #   run tg2fibery
    #   assert that telegram content got into Fibery
    # v1: read from telegram
    with telegram(message="autogenerated") as tg, fibery() as fbr:
        response = requests.get(url=f"{tg.address}/bot{tg.token}/getUpdates?limit=1")
        assert response.status_code == 200

        response = requests.post(
            url=f"{fbr.address}/api/commands",
            headers={
                "Authorization": f"Token {fbr.token}",
                "Content-Type": "application/json",
            },
            json=[
                {
                    "command": "fibery.entity/create",
                    "args": {
                        "type": "Knowledge Management/Material",
                        "entity": {
                            "fibery/id": "abcd",
                        },
                    },
                }
            ],
        )
        assert response.status_code == 200
