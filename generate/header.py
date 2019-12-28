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


Document = typing.Dict[str, typing.Any]
GraphPattern = typing.Union[typing.List[Document], Document]


class Operator:
    pass


class QueryException(Exception):
    pass


@dataclass
class BasePath:
    step: dict

    def __str__(self) -> str:
        return json.dumps({"@context": CONTEXT, **self.step})


@dataclass
class FinalPath(BasePath):
    pass


@dataclass
class Path(BasePath):
    pass

