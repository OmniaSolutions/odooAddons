# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2020 OmniaSolutions (<https://www.omniasolutions.website>). All Rights Reserved
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
    'name': 'Sale Order Mandatory Product',
    'version': '14.0',
    'author': 'OmniaSolutions',
    'website': 'https://www.omniasolutions.website',
    'category': 'Sales/Sales',
    'sequence': 15,
    'summary': 'Allows mandatory Product to be added automatically on sale order line',
    'images': [],
    'depends': ['sale'],
    'description': """ 
    This module extend the capability of the product to allows adding some mandatory products.
    so if you select in the sale.order.line a product that contain a mandatory product, a ney sale order line with the mandatory product
    will be created.
    also if you change the qty of a mandatory product also the parent mandatory product quantity will be changed
    """,
    'data': [
             'views/product_template.xml',
             'views/product_product.xml',
       ],
    'demo': [
        ],
    'test': [
        ],
    'installable': False,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
