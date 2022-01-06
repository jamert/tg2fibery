#!/usr/bin/env python
import configparser

from attr import define

@define
class Telegram:
    token: str


def get_token():
    parser = configparser.ConfigParser()
    parser.read("secrets.ini", encoding="utf-8")
    return parser.get(section="telegram", option="token")


def main():
    print(Telegram(token=get_token()))


if __name__ == "__main__":
    main()
