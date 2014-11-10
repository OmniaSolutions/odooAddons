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
    'name': 'omnia_website',
    'version': '0.1',
    'category': 'Custom',
    'sequence': 2,
    'description': """
Manage Website
====================
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['web','website_sale'],
    'data': [
             #view
             'view/omnia_website.xml',
             'view/omnia_product.xml'
    ],
    #'js': ['static/src/js/website_sale_omnia.js'],
    #'js':'omnia_website/static/src/js/website_sale_omnia.js',
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application':True,
    'auto_install': False,
}

