# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
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
    'name': 'omnia_DDT',
    'version': '0.0',
    'category': 'Custom',
    'description': """
Manage DDT documents
====================
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['stock','delivery','report_webkit'],
    'data': [
             #view
             'view/carriage_condition_data.xml',
             'view/carriage_condition_view.xml',
             'view/goods_description_data.xml',
             'view/goods_description_view.xml',
             
             
             'view/picking_view.xml',
             'view/sequence.xml',
             'view/transportation_reason_data.xml',
             'view/transportation_reason_view.xml',
             'view/acc_invoice_view_ddt.xml',
             #report
             'report/report_omnia_account_invoice.xml',
             #menu
             'menu_configuration.xml',
             #security
             'security/ddt_groups.xml',
             'security/ir.model.access.csv',
             
    ],
    'installable': True,
    'auto_install': False,
}

