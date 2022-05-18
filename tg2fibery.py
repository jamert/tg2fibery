#!/usr/bin/env python
import configparser

import click
from attr import define


@define
class Telegram:
    token: str


def get_token(config_string: str) -> str:
    parser = configparser.ConfigParser()
    parser.read_string(config_string)
    return parser.get(section="telegram", option="token")


@click.command
@click.option(
    "--secret", type=click.Path(exists=True, dir_okay=False), default="secrets.ini"
)
def main(secret: str) -> None:
    with open(secret, "rt") as fd:
        print(Telegram(token=get_token(fd.read())))


if __name__ == "__main__":
    main()
