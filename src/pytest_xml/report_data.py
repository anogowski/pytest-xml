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

from _pytest.config import Config
from pytest_item_dict.plugin import ItemDictPlugin, ITEM_DICT_PLUGIN_NAME


@dataclass
class Report_Data:

	def __init__(self, config: Config) -> None:
		self._config: Config = config

		self._total_duration: float = 0
		self._num_collected_items: int = 0
		self._collected_items: list[Item] = []
		self._running_state: str = "not_started"
		self.items_dict_plugin: ItemDictPlugin = self.config.pluginmanager.get_plugin(name=ITEM_DICT_PLUGIN_NAME)

		self._additional_summary: dict[str, list[Any]] = {
		    "prefix": [],
		    "summary": [],
		    "postfix": [],
		}

		self._sections: list[str] = ["metadata", "summary", "results"]

		self._data: dict[str, Any] = {
		    "environment": {},
		    "tests": defaultdict(list),
		}

		self._outcomes: dict[str, dict[str, str | int]] = {
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
		    "unexecuted": {
		        "label": "Unexecuted",
		        "value": 0
		    }
		}

	@property
	def get_kwargs(self) -> dict[str, int]:
		replace_dict: dict[str, str] = {
		    "Failed": "total_fail",
		    "Passed": "total_pass",
		    "Skipped": "total_skip",
		    "Expected failures": "total_ex_fail",
		    "Unexpected passes": "total_unpass",
		    "Errors": "total_errors",
		    "Reruns": "total_reruns",
		    "Unexecuted": "total_unexecuted",
		}
		report_kwargs: dict[str, int] = {}
		for key, value in self._outcomes.items():
			label: str = str(self._outcomes[key]["label"])
			num_outcomes: int = int(self._outcomes[key]['value'])
			report_kwargs[replace_dict[label]] = num_outcomes
		return report_kwargs

	@property
	def config(self) -> Config:
		return self._config

	@property
	def total_duration(self) -> float:
		return self._total_duration

	@total_duration.setter
	def total_duration(self, duration) -> None:
		self._total_duration = duration

	@property
	def num_collected_items(self) -> int:
		return self._num_collected_items

	@num_collected_items.setter
	def num_collected_items(self, count: int) -> None:
		self._num_collected_items = count

	@property
	def collected_items(self) -> list[Item]:
		return self._collected_items

	@collected_items.setter
	def collected_items(self, items: list[Item]) -> None:
		self._collected_items = items

	@property
	def collected_nodeids(self) -> list[str]:
		return [item.nodeid for item in self._collected_items]

	@property
	def collection_hierarchy(self) -> dict[str, Any]:
		self.items_dict_plugin = self.config.pluginmanager.get_plugin(name=ITEM_DICT_PLUGIN_NAME)
		if self.items_dict_plugin is not None:
			return self.items_dict_plugin.collect_dict.hierarchy
		return {}

	@property
	def test_hierarchy(self) -> dict[str, Any]:
		self.items_dict_plugin = self.config.pluginmanager.get_plugin(name=ITEM_DICT_PLUGIN_NAME)
		if self.items_dict_plugin is not None:
			return self.items_dict_plugin.test_dict.hierarchy
		return {}

	@property
	def running_state(self) -> str:
		return self._running_state

	@running_state.setter
	def running_state(self, state) -> None:
		self._running_state = state

	@property
	def additional_summary(self) -> dict[str, list[Any]]:
		return self._additional_summary

	@additional_summary.setter
	def additional_summary(self, value) -> None:
		self._additional_summary = value

	@property
	def sections(self) -> list[str]:
		return self._sections

	@sections.setter
	def sections(self, sections) -> None:
		self._sections = sections

	@property
	def data(self) -> dict[str, Any]:
		return self._data

	@property
	def title(self):
		return self._data["title"]

	@title.setter
	def title(self, title):
		self._data["title"] = title

	@property
	def outcomes(self) -> dict[str, dict[str, Any]]:
		return self._outcomes

	@outcomes.setter
	def outcomes(self, outcome) -> None:
		self._outcomes[outcome.lower()]["value"] += 1

	def set_data(self, key, value) -> None:
		self._data[key] = value

	def add_test(self, report, outcome):
		# passed "setup" and "teardown" are not added to the xml
		if report.when == "collect":
			self._data["tests"][report.nodeid.replace("::", "-")].append(outcome)

		elif report.when == "call":
			self.outcomes = outcome
			self._data["tests"][report.nodeid.replace("::", "-")].append(outcome)
