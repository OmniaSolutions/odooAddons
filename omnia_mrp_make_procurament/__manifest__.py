# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Omnia Mrp Make Procurement',
    'version': '12.0.3',
    'sequence': 1,
    'category': 'Custom',
    'description': """
Allow the capability to recursively make procurement order from manufactoring order on all levels
""",
    'author': 'OmniaSolutions',
    'maintainer': 'OmniaSolutions',
    'website': 'https://www.omniasolutions.website',
    'images': ['static/img/mrp_make_procurement.png'],
    'depends': ['base',
                'mrp',
                'stock',
                'purchase',
                'purchase_stock',
                'omnia_mrp_analytic'],
    'data': [
        #  view
        'views/mrp_production.xml',
        'views/purchase_order.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
