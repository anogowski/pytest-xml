# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Python Includes
import datetime
import json
import math
import os
import re
import time
from typing import Final
from pathlib import Path
from collections import defaultdict
from typing import Any

# Pip Includes
from jinja2 import Template
from data_to_xml.xml_converter import XMLConverter

# Pytest Includes
import pytest
from pytest import CollectReport, Item, Session, TestReport
from pytest_metadata.plugin import metadata_key

from _pytest.config import Config, Notset
from _pytest.config.argparsing import Parser
from _pytest.terminal import TerminalReporter

from pytest_item_dict.plugin import ItemDictPlugin

# Plugin Includes
from pytest_xml.version import __version__
from pytest_xml.report_data import Report_Data


class XML_Report:
	ENVIRONMENT_METADATA: Final[list[str]] = ['environment', 'JAVA_HOME', 'Packages', 'Platform', 'Plugins', 'Python']
	ENVIRONMENT_STR: Final[str] = 'environment'

	def __init__(self, report_path: str, config: Config, report_data: Report_Data, template: Template) -> None:
		self._report_path: Path = (Path.cwd() / Path(os.path.expandvars(path=report_path)).expanduser())
		self._report_path.parent.mkdir(parents=True, exist_ok=True)
		self._config: Config = config
		self._max_asset_filename_length: int = int(str(config.getini(name="max_asset_filename_length")))

		self._reports = defaultdict(dict)
		self._report: Report_Data = report_data
		self._report.title = self._report_path.name
		self._suite_start_time: float = time.time()

		self._template: Template = template

	def _to_xml(self, data: dict, root_node: str | None = None) -> str:
		"""Converts the data dictionary into xml and returns it.

		Args:
			data (dict): dictionary to convert to xml

		Returns:
			str: xml of data dictionary
		"""
		return XMLConverter(my_dict=data, root_node=root_node).formatted_xml if len(data.keys()) > 0 else ""

	def _generate_report(self):
		"""Formats the report 
		"""
		generated: datetime.datetime = datetime.datetime.now()
		num_collected_items, current_test_count, duration = self._run_count()
		# test_data: str = json.dumps(self._report.data)
		metadata_dict: dict[Any, Any] = self._config.stash[metadata_key]
		env_metadata: dict = {i: metadata_dict[i] for i in metadata_dict if i in self.ENVIRONMENT_METADATA}
		non_env_metadata: dict = {i: metadata_dict[i] for i in metadata_dict if i not in self.ENVIRONMENT_METADATA}
		rendered_report: str = self._template.render(
		    self._report.get_kwargs,
		    # self._report.additional_summary,
		    title=self._report.title,
		    report_date=generated.strftime("%d-%b-%Y"),
		    report_time=generated.strftime("%H:%M:%S"),
		    pytest_xml_version=__version__,
		    environment=self._to_xml(data=env_metadata, root_node="report-environment"),
		    metadata=self._to_xml(data=non_env_metadata, root_node="report-metadata"),
		    additional_summary=self._to_xml(data=self._report.additional_summary, root_node="report-summary"),
		    running_state=self._report.running_state,
		    tests_to_run=num_collected_items,
		    tests_ran=current_test_count,
		    total_duration=duration,
		    collected_tests=self._to_xml(data=self._report.collection_hierarchy, root_node="report-collected-tests"),
		    hierarchy=self._to_xml(data=self._report.test_hierarchy, root_node="report-test-status"),
		)

		output_file: str = Path(f"{__file__}/../../../output/reports/collect.xml").as_posix()

		with open(output_file, "w+") as f:
			xml_doc: list[str] = [
			    r'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + '\n',
			    r'<collect-report>',
			    self._to_xml(data=self._report.collection_hierarchy),
			    r'</collect-report>',
			]
			f.writelines(xml_doc)

		self._write_report(rendered_report)

	def _generate_environment(self) -> dict[Any, Any]:
		metadata: dict[Any, Any] = self._config.stash[metadata_key]

		for key in metadata.keys():
			value = metadata[key]
			if self._is_redactable_environment_variable(key):
				black_box_ascii_value = 0x2593
				metadata[key] = "".join(chr(black_box_ascii_value) for _ in str(value))

		return metadata

	def _is_redactable_environment_variable(self, environment_variable) -> bool:
		redactable_regexes: list[str] | str = self._config.getini(name="environment_table_redact_list")  #type: ignore
		for redactable_regex in redactable_regexes:
			if re.match(redactable_regex, environment_variable):
				return True

		return False

	def _write_report(self, rendered_report: str) -> None:
		"""Writes the report

		Args:
			rendered_report (str): xml to be written
		"""
		with self._report_path.open("w", encoding="utf-8") as f:
			f.write(rendered_report)

	def _run_count(self) -> tuple[int, int, str]:
		"""- total number of tests to run
		- current number of tests ran
		- current duration of tests ran

		Returns:
			tuple[int, int, str]: collected_items, current_test_count, duration
		"""
		relevant_outcomes: list[str] = ["passed", "failed", "xpassed", "xfailed"]
		current_test_count: int = 0
		for outcome in self._report.outcomes.keys():
			if outcome in relevant_outcomes:
				current_test_count += self._report.outcomes[outcome]["value"]

		duration: str = _format_duration(duration=self._report.total_duration)

		return self._report.num_collected_items, current_test_count, duration

	@pytest.hookimpl(trylast=True)
	def pytest_sessionstart(self, session):
		self._report.set_data("environment", self._generate_environment())

		session.config.hook.pytest_xml_report_title(report=self._report)

		self._report.running_state = "started"
		if self._config.getini("generate_report_on_test"):
			self._generate_report()

	@pytest.hookimpl(trylast=True)
	def pytest_sessionfinish(self, session):
		session.config.hook.pytest_xml_results_summary(
		    prefix=self._report.additional_summary["prefix"],
		    summary=self._report.additional_summary["summary"],
		    postfix=self._report.additional_summary["postfix"],
		    session=session,
		)
		self._report.running_state = "finished"
		suite_stop_time: float = time.time()
		self._report.total_duration = suite_stop_time - self._suite_start_time
		self._generate_report()

	@pytest.hookimpl(trylast=True)
	def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
		"""Print the location of the report at the end of testing

		Args:
			terminalreporter (TerminalReporter): Object used to write terminal output
		"""
		terminalreporter.write_sep(
		    sep="-",
		    title=f"Generated xml report: {self._report_path.as_uri()}",
		)

	@pytest.hookimpl(trylast=True)
	def pytest_collectreport(self, report: CollectReport) -> None:
		if report.failed:
			self._process_report(report=report, duration=0, processed_extras=[])

	@pytest.hookimpl(trylast=True)
	def pytest_collection_finish(self, session: Session):
		self._report.collected_items = session.items
		self._report.num_collected_items = len(session.items)

	@pytest.hookimpl(trylast=True)
	def pytest_runtest_logreport(self, report: TestReport):
		# "reruns" makes this code a mess.
		# We store each combination of when and outcome
		# exactly once, unless that outcome is a "rerun"
		# then we store all of them.
		key: tuple[Any, Any] = (report.when, report.outcome)
		if report.outcome == "rerun":
			if key not in self._reports[report.nodeid]:
				self._reports[report.nodeid][key] = list()
			self._reports[report.nodeid][key].append(report)
		else:
			self._reports[report.nodeid][key] = [report]

		finished = report.when == "teardown" and report.outcome != "rerun"
		if not finished:
			return

		# Calculate total duration for a single test.
		# This is needed to add the "teardown" duration
		# to tests total duration.
		test_duration = 0
		for key, reports in self._reports[report.nodeid].items():
			_, outcome = key
			if outcome != "rerun":
				test_duration += reports[0].duration

		processed_extras = []
		for key, reports in self._reports[report.nodeid].items():
			when, _ = key
			for each in reports:
				test_id = report.nodeid
				if when != "call":
					test_id += f"::{when}"
				# processed_extras += self._process_extras(each, test_id)

		for key, reports in self._reports[report.nodeid].items():
			when, _ = key
			for each in reports:
				dur = test_duration if when == "call" else each.duration
				self._process_report(each, dur, processed_extras)

		if self._config.getini("generate_report_on_test"):
			self._generate_report()

	def _process_report(self, report, duration, processed_extras):
		outcome = _process_outcome(report)
		try:
			# hook returns as list for some reason
			formatted_duration = self._config.hook.pytest_xml_duration_format(duration=duration)[0]
		except IndexError:
			formatted_duration = _format_duration(duration)

		self._report.add_test(report=report, outcome=outcome)


def _format_duration(duration):
	if duration < 1:
		return "{} ms".format(round(duration * 1000))

	hours = math.floor(duration / 3600)
	remaining_seconds = duration % 3600
	minutes = math.floor(remaining_seconds / 60)
	remaining_seconds = remaining_seconds % 60
	seconds = round(remaining_seconds)

	return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _is_error(report: TestReport) -> bool:
	return (report.when in ["setup", "teardown", "collect"] and report.outcome == "failed")


def _process_outcome(report) -> str:
	if _is_error(report):
		return "Error"
	if hasattr(report, "wasxfail"):
		if report.outcome in ["passed", "failed"]:
			return "XPassed"
		if report.outcome == "skipped":
			return "XFailed"

	return report.outcome.capitalize()
