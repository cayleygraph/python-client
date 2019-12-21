import json
import time
import logging
from operator import itemgetter
from typing import Optional, Iterable
from enum import Enum
from dataclasses import dataclass, field

import requests
from requests.exceptions import ConnectionError, HTTPError

from .path import Path
from .languages import QueryLanguage
from .content_types import QueryContentType


DEFAULT_CONNECT_TIMEOUT = 30
DEFAULT_CONNECT_INTERVAL = 0.1


logger = logging.getLogger(__name__)


@dataclass
class Client:
    endpoint: str = "http://localhost:64210"
    session: requests.Session = field(init=False, default_factory=requests.session)
    connected: bool = field(init=False, default=False)

    def is_available(self, verbose: bool = False) -> bool:
        try:
            res = self.session.get(self.endpoint)
            res.raise_for_status()
            return True
        except (ConnectionError, HTTPError) as error:
            if verbose:
                logger.error(error)
            return False

    def connect(
        self, timeout=DEFAULT_CONNECT_TIMEOUT, interval=DEFAULT_CONNECT_INTERVAL
    ) -> None:
        self.connected = False
        start = time.time()
        while start + timeout > time.time():
            if self.is_available():
                self.connected = True
                return
            time.sleep(interval)
        raise ConnectionError

    def _ensure_connection(self) -> None:
        if not self.connected:
            self.connect()

    # TODO don't get prefixed uris
    def read(
        self,
        sub: Optional[str] = None,
        pred: Optional[str] = None,
        obj: Optional[str] = None,
        label: Optional[str] = None,
    ) -> requests.Response:
        self._ensure_connection()
        params = {"iri": "full"}
        if sub is not None:
            params["sub"] = sub
        if pred is not None:
            params["pred"] = pred
        if obj is not None:
            params["obj"] = obj
        if label is not None:
            params["label"] = label
        res = self.session.get(
            self.endpoint + "/api/v2/read", stream=True, params=params
        )
        res.raise_for_status()
        return res

    def query(
        self,
        query: str,
        language: QueryLanguage,
        content_type: Optional[QueryContentType] = None,
    ) -> requests.Response:
        self._ensure_connection()
        headers = {}
        if content_type:
            headers["Accept"] = content_type.value
        res = self.session.post(
            self.endpoint + f"/api/v2/query",
            data=str(query),
            headers=headers,
            params={"lang": language.value},
        )
        res.raise_for_status()
        return res

    def close(self):
        self.session.close()
