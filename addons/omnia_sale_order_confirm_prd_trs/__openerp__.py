# -*- coding: utf-8 -*-
##############################################################################
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
    'name': 'omnia_sale_order_confirm_prd_trs',
    'version': '0.1',
    'category': 'Custom',
    'sequence':1,
    'short_desc': 'Omnia Sale Order Confirm Product Transfer',
    'description': """ """,
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['sale'],
    'data': [
             #view
            'views/product_category.xml',
            'views/sequence.xml',
            'views/inventory_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application':False,
}

