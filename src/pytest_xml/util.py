# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from jinja2 import Environment, Template
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape


def _read_template(search_paths, template_name="xml_template.xml.jinja") -> Template:
	env = Environment(
	    loader=FileSystemLoader(searchpath=search_paths),
	    autoescape=select_autoescape(enabled_extensions=("jinja2",),),
	)
	return env.get_template(name=template_name)
