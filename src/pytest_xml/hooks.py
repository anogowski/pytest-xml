# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def pytest_xml_report_title(report):
	"""Called before adding the title to the report"""


def pytest_xml_results_summary(summary, session):
	"""Called before adding the summary section to the report"""


def pytest_xml_duration_format(duration: str):
	"""Called before using the default duration formatting."""
