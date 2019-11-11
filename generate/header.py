"""
The base module for the generated path module.
Guidelines:
 - Import modules, not names for explicitness about external dependencies
"""
import json
import typing
import rdflib.term

from .languages import QueryLanguage

if typing.TYPE_CHECKING:
    from .client import Client


class Operator:
    pass


class QueryException(Exception):
    pass


class Path:
    __cursor: typing.Optional[dict]

    def __init__(self, client: "Client") -> None:
        self.client = client
        self.__cursor = None

    def __add_step(self, step: dict) -> None:
        prev_cursor = self.__cursor
        self.__cursor = step
        if prev_cursor:
            self.__cursor = {**self.__cursor, "linkedql:from": prev_cursor}

    def __execute(self):
        res = self.client.query(
            json.dumps(self.__cursor), QueryLanguage.linkedql, QueryContentType.json_ld
        )
        res = res.json()
        if "error" in res:
            raise QueryException(res["error"])
        return res["result"]

    def __iter__(self) -> typing.Iterator:
        return iter(self.__execute())

