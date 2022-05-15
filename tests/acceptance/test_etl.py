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

        self.material_id = "90c6d940-ce27-11ec-b591-698a572b9bd4"
        self.material_praise_update_secret = "b33a25d1-99ba-11e9-8c59-09d0cb6f3aeb"

    def setup(self) -> None:
        requests.post(
            url=f"{mountebank_address}/imposters",
            json={
                "port": self._port,
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
        return {
            "responses": [
                {
                    "is": {
                        "statusCode": 200,
                        "body": {
                            "success": True,
                            "result": {
                                "fibery/id": self.material_id,
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

    def get_material_praise_secret(self) -> dict:
        return {
            "responses": [
                {
                    "is": {
                        "statusCode": 200,
                        "body": {
                            "success": True,
                            "result": [
                                {
                                    "fibery/id": self.material_id,
                                    "Knowledge Management/Praise": {
                                        "Collaboration~Documents/secret": self.material_praise_update_secret
                                    },
                                }
                            ],
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
                                "command": "fibery.entity/query",
                                "args": {
                                    "q/from": "Knowledge Management/Material",
                                    "q/select": [
                                        "fibery/id",
                                        {
                                            "Knowledge Management/Praise": [
                                                "Collaboration~Document/secret"
                                            ]
                                        },
                                    ],
                                    "q/where": ["=", '["fibery/id"]', "$id"],
                                    "q/limit": 1,
                                },
                                "params": {"$id": self.material_id},
                            }
                        ],
                    },
                },
            ],
        }

    def update_material_praise(self) -> dict:
        return {
            "responses": [
                {
                    "is": {
                        "statusCode": 200,
                    }
                }
            ],
            "predicates": [
                {
                    "equals": {
                        "method": "PUT",
                        "path": f"/api/documents/{self.material_praise_update_secret}",
                        "query": {"format": "md"},
                        "headers": {
                            "Authorization": f"Token {self.token}",
                            "Content-Type": "application/json",
                        },
                    },
                    "exists": {
                        "body": {"content": True},
                    },
                },
            ],
        }

    def teardown(self) -> None:
        requests.delete(url=f"{mountebank_address}/imposters/{self._port}")

    def compare_content(self, content: str) -> bool:
        response = requests.get(url=f"{mountebank_address}/imposters/{self._port}")
        return any(
            content == request.get("body", {}).get("content")
            for request in response.json()["requests"]
        )


def test_etl():
    text = "autogenerated"

    with telegram(message=text) as tg, fibery() as fbr:
        # run etl with prepared secrets
        assert fbr.compare_content(text)
