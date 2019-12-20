"""
The base module for the generated path module.
Guidelines:
 - Import modules, not names for explicitness about external dependencies
"""
import json
import typing
import rdflib.term
from dataclasses import dataclass

from .languages import QueryLanguage
from .content_types import QueryContentType


class Operator:
    pass


class QueryException(Exception):
    pass


@dataclass
class BasePath:
    cursor: typing.Optional[dict] = None

    def __str__(self) -> str:
        return json.dumps(self.cursor)


@dataclass
class FinalPath(BasePath):
    pass


@dataclass
class Path(BasePath):
    def __add_final_step(self, step: dict) -> "FinalPath":
        return FinalPath({**step, "linkedql:from": self.cursor})

    def __add_step(self, step: dict) -> "Path":
        return Path({**step, "linkedql:from": self.cursor})

