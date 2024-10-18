# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Python Includes
from dataclasses import dataclass
from typing import Any
from collections import defaultdict

# Pytest Includes
import pytest
from pytest import Item
from pytest_metadata.plugin import metadata_key

from _pytest.config import Config, Notset
from _pytest.config.argparsing import Parser


@dataclass
class Report_Data:

	def __init__(self, config: Config) -> None:

		self._total_duration: float = 0
		self._collected_items: int = 0
		self._running_state: str = "not_started"

		self._config: Config = config

		self._sections: list[str] = ["metadata", "summary", "results"]

		self._data: dict[str, Any] = {
		    "environment": {},
		    "tests": defaultdict(list),
		}

		self._outcomes: dict[str, dict[str, Any]] = {
		    "failed": {
		        "label": "Failed",
		        "value": 0
		    },
		    "passed": {
		        "label": "Passed",
		        "value": 0
		    },
		    "skipped": {
		        "label": "Skipped",
		        "value": 0
		    },
		    "xfailed": {
		        "label": "Expected failures",
		        "value": 0
		    },
		    "xpassed": {
		        "label": "Unexpected passes",
		        "value": 0
		    },
		    "error": {
		        "label": "Errors",
		        "value": 0
		    },
		    "rerun": {
		        "label": "Reruns",
		        "value": 0
		    },
		}

	@property
	def total_duration(self) -> float:
		return self._total_duration

	@total_duration.setter
	def total_duration(self, duration) -> None:
		self._total_duration = duration

	@property
	def collected_items(self) -> int:
		return self._collected_items

	@collected_items.setter
	def collected_items(self, count: int) -> None:
		self._collected_items = count

	@property
	def sections(self) -> list[str]:
		return self._sections

	@sections.setter
	def sections(self, sections) -> None:
		self._sections = sections

	@property
	def config(self) -> Config:
		return self._config

	@property
	def outcomes(self) -> dict[str, dict[str, Any]]:
		return self._outcomes

	@outcomes.setter
	def outcomes(self, outcome) -> None:
		self._outcomes[outcome.lower()]["value"] += 1

	def set_data(self, key, value) -> None:
		self._data[key] = value

	def add_test(self, report, outcome):
		# passed "setup" and "teardown" are not added to the html
		if report.when in ["call", "collect"]:
			self.outcomes = outcome
			self._data["tests"][report.nodeid].append(outcome)
