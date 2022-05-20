#!/usr/bin/env python
import configparser
from typing import List

import click
import requests
from attr import define


@define
class TelegramUpdate:
    update_id: int
    content: str  # message->text

    @classmethod
    def from_api_response(cls, value: list) -> List["TelegramUpdate"]:
        return [
            cls(u["update_id"], u["message"]["text"]) for u in value if "message" in u
        ]


@define
class Telegram:
    netloc: str
    token: str

    def fetch_updates(self) -> List[TelegramUpdate]:
        response = requests.get(
            url=f"{self.netloc}/bot{self.token}/getUpdates?limit=1",
            headers={
                "Content-Type": "application/json",
            },
        )
        return TelegramUpdate.from_api_response(response.json())


class Config:
    def __init__(self, filename: str) -> None:
        self.parser = configparser.ConfigParser()
        self.parser.read(filename)

    def secrets(self, section: str) -> dict:
        return dict(self.parser[section])


@click.command
@click.option(
    "--secret", type=click.Path(exists=True, dir_okay=False), default="secrets.ini"
)
def main(secret: str) -> None:
    print(Telegram(**Config(secret).secrets("telegram")).fetch_updates())


if __name__ == "__main__":
    main()
