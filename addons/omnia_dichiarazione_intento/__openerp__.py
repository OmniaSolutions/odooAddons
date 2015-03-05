# -*- coding: utf-8 -*-
##############################################################################
#
#
#    Author : Matteo Boscolo  (Omniasolutions)
#    mail:Matteo Boscolo@omniasolutions.eu
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
    'name': 'omnia_dichiarazione_intento',
    'version': '0.1',
    'category': 'accounting',
    'description': """
Manage Dichiarazione D'Intento (Italian Accounting Vat declaration for EU company )
===================================================================================
""",
    'author'    : 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website'   : 'http://www.OmniaSolutions.eu',
    'depends'   : ['account'],
    'data'      : [
                 #view
                 'view/dichiarazione_intento.xml',
                 'view/res_partner.xml',
                 ],
    'installable': True,
    'auto_install': False,
}

