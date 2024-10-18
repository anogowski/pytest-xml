# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Python Includes
import logging
from typing import Any, Final
from enum import StrEnum
from pathlib import Path

# Pytest Includes
import pytest
from pytest import Item, CallInfo
from pytest_metadata.plugin import metadata_key

from _pytest.config import Config, Notset
from _pytest.config.argparsing import Parser
from _pytest.reports import TestReport

# Plugin Includes
from .report_data import Report_Data
from .xml_report import XML_Report


def pytest_addoption(parser: Parser):
	group: pytest.OptionGroup = parser.getgroup(name='xml')
	group.addoption('--xml', action='store', dest='xml_path', metavar="path", default=None, help='create xml report file at given path.')

	parser.addini(
	    name="max_asset_filename_length",
	    type="string",
	    default=255,
	    help="set the maximum filename length for assets "
	    "attached to the xml report.",
	)

	parser.addini(
	    name="environment_table_redact_list",
	    type="linelist",
	    help="a list of regexes corresponding to environment "
	    "table variables whose values should be redacted from the report",
	)

	parser.addini(
	    name="generate_report_on_test",
	    type="bool",
	    default=False,
	    help="the xml report will be generated after each test "
	    "instead of at the end of the run.",
	)


def pytest_configure(config: Config) -> None:
	xml_path: Path | Notset = config.getoption(name="xml_path")

	# prevent opening html_path on worker nodes (xdist)
	if isinstance(xml_path, Path) and not hasattr(config, "workerinput"):
		report_data: Report_Data = Report_Data(config=config)
		xml: XML_Report = XML_Report(report_path=xml_path, config=config, report_data=report_data)

		config.pluginmanager.register(plugin=xml)


def pytest_unconfigure(config: Config):
	xml: object | None = config.pluginmanager.getplugin(name="xml")
	if xml is not None:
		config.pluginmanager.unregister(plugin=xml)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo):
	outcome: Any = yield
	report: TestReport = outcome.get_result()
	if report.when == "call":
		...
