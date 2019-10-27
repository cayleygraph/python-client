import json
from typing import List, Iterator, TYPE_CHECKING
from rdflib.term import Node

from .languages import QueryLanguage

if TYPE_CHECKING:
    from .client import Client

class Operator:
    pass

class QueryException(Exception):
    pass

class Path:
    def __init__(self, client: 'Client') -> None:
        self.client = client
        self.__cursor = None

    def __add_step(self, step: dict) -> None:
        prev_cursor = self.__cursor
        self.__cursor = step
        if prev_cursor:
            self.__cursor = {**self.__cursor, "linkedql:from": prev_cursor}

    def __iter__(self) -> Iterator:
        res = self.client.query(json.dumps(self.__cursor), QueryLanguage.linkedql, QueryContentType.json_ld)
        res = res.json()
        if "error" in res:
            raise QueryException(res["error"])
        return res["result"]

