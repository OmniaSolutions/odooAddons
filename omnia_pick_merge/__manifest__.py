# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Author : Matteo Boscolo  (Omniasolutions)
#    mail:matteo.boscolo@omniasolutions.eu
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
#    All Right Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'omnia_pick_merge',
    'version': '10.0.1.1.0',
    'sequence': 1,
    'category': 'Custom',
    'description': """
merge picking
====================
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['sale',
                'stock',],
    'license': 'AGPL-3',
    'data': ['views/stock_picking.xml',
             'wizard/wizard.xml',
             # report
             #'report/report_ddt.xml',
             # menu
             #'view/menu_configuration.xml',
             # security
             #'security/ddt_groups.xml',
             ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
