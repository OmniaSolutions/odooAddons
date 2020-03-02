##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2020 OmniaSolutions (<https://omniasolutions.website>). All Rights Reserved
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
# Leonardo Cazziolati
# leonardo.cazziolati@omniasolutions.eu
# 28-02-2020

{
    'name': "Omnia Customer Servers",
    'version': '10.0.1',
    'author': 'OmniaSolutions',
    'website': 'https://www.omniasolutions.website',
    'category': 'Custom',
    'summary': 'Server configuration integration',
    'description': """This module integrates the ability to manage server configurations of your customers, implementing a dedicated item in the contacts module.""",
    
    'images': ['static/img/omnia_customer_servers.png'],
    
    'depends': ['base', 'contacts'],

    'data': [
        'security/new_group.xml',
        'views/server_view.xml',
        'security/ir.model.access.csv',
    ],
}