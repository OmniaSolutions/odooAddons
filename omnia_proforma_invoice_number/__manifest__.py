# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Author : Matteo Boscolo  (Omniasolutions)
#    mail:matteo.boscolo@omniasolutions.eu
#    Copyright (c) 2022 Omniasolutions (https://www.omniasolutions.website)
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
    'name': 'omnia_proforma_invoice_number',
    'version': '16.0.1',
    'sequence': 1,
    'category': 'invoice',
    'description': """
Add ProForma invoice number to the sale order
=============================================
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'https://www.OmniaSolutions.website',
    "license": "LGPL-3",
    "summary": "Pro Forma invoice number on sale order",
    "images": ["static/img/odoo_plm.png"],
    'depends': ['sale'],
    'data': ['views/sale_order.xml',
             # report
             'report/proforma_sale_order.xml',
             # data
             'data/ir_sequence.xml',
             ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
