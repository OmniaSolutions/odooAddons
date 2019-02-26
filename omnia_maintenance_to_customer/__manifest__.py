# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Maintenance to customer',
    'version': '11.0',
    'author': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.eu',
    'category': 'maintenance',
    'sequence': 15,
    'summary': 'Extend maintenance to the customer',
    'images': [],
    'depends': ['sale', 'maintenance'],
    'description': """
Extend maintenance to the customer
==============================================
    """,
    'data': [
            # security
            # 'security/my.xml',
            # views
            'views/maintenance.xml',
            # Reports Template
            # 'report_template/bom_structure_report_template.xml',
            # Report
            # 'report/bom_structure.xml',
            ],
#    'qweb': ['views/templates.xml'],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
