"""
The base module for the generated path module.
Guidelines:
 - Import modules, not names for explicitness about external dependencies
"""
import json
import typing
from copy import copy
from dataclasses import dataclass

import rdflib.term

from .content_types import QueryContentType
from .languages import QueryLanguage


CONTEXT = {"linkedql": "http://cayley.io/linkedql#"}


class Operator:
    pass


class QueryException(Exception):
    pass


@dataclass
class BasePath:
    cursor: typing.Optional[dict] = None

    def __str__(self) -> str:
        return json.dumps({"@context": CONTEXT, **self.cursor})


@dataclass
class FinalPath(BasePath):
    pass


@dataclass
class Path(BasePath):
    def __add_final_step(self, step: dict) -> "FinalPath":
        if self.cursor is None:
            raise RuntimeError(
                f"Can not call step {step['@id']} before calling another step first"
            )
        return FinalPath({**step, "linkedql:from": self.cursor})

    def __add_step(self, step: dict) -> "Path":
        new_step = copy(step)
        if self.cursor:
            new_step["linkedql:from"] = self.cursor
        return Path(new_step)
