#!/usr/bin/env python
import configparser

import click
from attr import define


@define
class Telegram:
    token: str


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
    print(Telegram(**Config(secret).secrets("telegram")))


if __name__ == "__main__":
    main()
