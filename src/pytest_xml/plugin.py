# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Python Includes
import logging
from typing import Any, Final
from enum import StrEnum
from pathlib import Path

# Pytest Includes
from jinja2 import Template
from pluggy import PluginManager
import pytest
from pytest import Item, CallInfo
from pytest_metadata.plugin import metadata_key

from _pytest.config import Config, Notset
from _pytest.config.argparsing import Parser
from _pytest.reports import TestReport

# Plugin Includes
from pytest_xml.report_data import Report_Data
from pytest_xml.xml_report import XML_Report
from pytest_xml.util import _read_template


def pytest_addhooks(pluginmanager: PluginManager):
	from pytest_xml import hooks

	pluginmanager.add_hookspecs(module_or_class=hooks)


def pytest_addoption(parser: Parser):
	group: pytest.OptionGroup = parser.getgroup(name='xml')
	group.addoption('--xml', action='store', dest='xml_path', metavar=str, default=None, help='create xml report file at given path.')

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
	resources_path: Path = Path(__file__).parent
	xml_path: str | Notset = config.getoption(name="xml_path")

	# prevent opening xml_path on worker nodes (xdist)
	if isinstance(xml_path, str) and not hasattr(config, "workerinput"):
		report_data: Report_Data = Report_Data(config=config)
		template: Template = _read_template(search_paths=[resources_path])
		xml: XML_Report = XML_Report(report_path=xml_path, config=config, report_data=report_data, template=template)

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
