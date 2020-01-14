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
    'name': 'Omnia Production Reordering Rule',
    'version': '10.0.1.2.0',
    'author': 'OmniaSolutions',
    'website': 'https://www.omniasolutions.website',
    'category': 'Production',
    'sequence': 15,
    'summary': 'Allows to create reordering in manufactory order creation',
    'images': [],
    'depends': ['mrp'],
    'description': """
    When a new production is created we check all the item of the manufactory order and we create the reordeing rule based on the wherehous present in the manufactory order
    we create automatically the rule only for the product that are marked as Automatic Reorder Rule
    """,
    'data': [
        'views/product_extension.xml',
        'views/mrp_production.xml'
            ],

    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
