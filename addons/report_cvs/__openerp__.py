# -*- coding: utf-8 -*-
##############################################################################
# this module is derived from the WebKitReport module made from camp2camp
# Copyright (c) 2010 OmniaSolutions (http://www.omniasolutions.eu)
# All Right Reserved
#
# Author : Daniel Smerghetto (OmniaSolutions)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name': 'cvs Report Engine',
    'description': """
This module adds a new Report Engine based on WebKit library (wkhtmltopdf) to support reports designed in HTML + CSS.
=====================================================================================================================

The module structure and some code is inspired by the report_openoffice module.


""",
    'version': '0.1',
    'depends': ['base'],
    'author': 'OmniaSolutions',
    'category': 'Reporting', # i.e a technical module, not shown in Application install menu
    'url': 'http://http://www.omniasolutions.eu/',
    'data': [ #'security/ir.model.access.csv',
              #'data.xml',
              #'wizard/report_webkit_actions_view.xml',
              #'company_view.xml',
              #'header_view.xml',
              'ir_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    #'images': ['images/companies_webkit.jpeg','images/header_html.jpeg','images/header_img.jpeg'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
