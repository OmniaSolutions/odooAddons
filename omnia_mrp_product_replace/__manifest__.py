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
    'name': '[OMNIASOLUTIONS] Product Bom replace',
    'version': '14.0.1',
    'sequence': 1,
    'category': 'Manufacturing',
    'description': """
================================================================================
This module allows you to replace a product with enother inside all the odoo bom
================================================================================
""",
 'author': 'mboscolo',
 'maintainer': 'https://www.OmniaSolutions.website',
 'website': 'https://www.OmniaSolutions.website',
 'depends': ['mrp','product'],
 'license': 'AGPL-3',
 'data': [#  view
          'views/product_product.xml',
          'views/product_template.xml',
          'wizard/wiz_product_replace.xml',
          #
          'security/security.xml'],
 'installable': True,
 'application': False,
 'auto_install': False,
}