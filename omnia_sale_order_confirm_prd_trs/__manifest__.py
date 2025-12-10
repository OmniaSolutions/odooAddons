# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2019 https://OmniaSolutions.website
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
    'name': 'omnia_sale_order_confirm_prd_trs',
    'version': '18.0.1.0.0',
    'category': 'Custom',
    'sequence': 1,
    'short_desc': 'Omnia Sale Order Confirm Product Transfer',
    'description': """ """,
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': [
        'sale',
        'purchase',
        'stock'
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/product_category.xml',
        'views/product_product.xml',
        'views/inventory_view.xml',
    ],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
