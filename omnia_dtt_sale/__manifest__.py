# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Matteo Boscolo  (Omniasolutions)
#    mail:matteo.boscolo@omniasolutions.eu
#    Copyright (c) 2022 Omniasolutions (http://www.omniasolutions.website) 
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
    'name': 'omnia_ddt_sale',
    'version': '14.0.1',
    'sequence': 1,
    'category': 'Custom',
    'description': """
New field on sale order to extend
=================================
""",
    'author': 'info@omniasolutions.eu',
    'maintainer': 'info@omniasolutions.eu',
    'website': 'http://www.OmniaSolutions.website',
    'depends': ['account','stock', 'delivery'],
    'data': [# view
             'view/sale_order.xml',
             # report
             'report/report_sale.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

