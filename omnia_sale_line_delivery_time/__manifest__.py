# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#
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
    'name': 'Sale Order Line Delivery Date',
    'version': '10.0.1.0',
    'author': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.eu',
    'description': 'Adds new field in Sale Order Line to manage product delivery date',
    'sequence': 15,
    'summary': 'Sale Order Customization',
    'depends': ['sale'],
    'category': "Sale",
    'data': ['views/sale_order.xml'],
    'installable': True,
}
