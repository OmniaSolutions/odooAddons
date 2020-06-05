# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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
    'name': 'Purchase Order chuse vendor',
    'version': '0.1',
    'author': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.eu',
    'category': 'Purchase',
    'sequence': 1,
    'summary': 'Allow to work on purchase order line and re assign the vendor with a custom action',
    'images': [''],
    'depends': ['purchase'],
    'description': """
This module allows you to re assign the vendor on the draft purchase order
==========================================================================
    """,
    'data': [
        # reports
        # views
        'views/purchase.xml'],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
