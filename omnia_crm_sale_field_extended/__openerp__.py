# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2017 OmniaSosutions S.N.C di Boscolo Matteo & C
#
#
#    Author : Matteo Boscolo
#    mail:matteo.boscolo@omniasolutions.eu
#    Copyright (c) 2017 Omniasolutions (http://www.omniasolutions.eu) 
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
    'name': 'omnia_crm_sale_field_extended',
    'version': '10.0.0.1.0',
    'sequence': 1,
    'category': 'CRM',
    'description': """
This module extend the integration between the crm and the sale module adding fields to the crm
================================================================================================
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['sale', 'crm'],
    'data': [
        #  view
        'view/crm_lead.xml',
        #  report
        #  'report/myReport.xml',
        #  menu
        #  'view/myMenu.xml',
        #  security
        # 'security/mySecurity.xml',
        # data
        'data/custom_filter.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
