# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 Omniasolutions.website
#    Author : Matteo Bsocolo  (Omniasolutions)
#    mail:matteo.boscolo@omniasolutions.eu
#    Copyright (c) 2019 Matteo Boscolo (https://www.omniasolutions.website) 
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
    'name': 'CBI Italian Bank Import',
    'version': '10.0.1.0.0',
    'sequence': 1,
    'category': 'Accounting',
    'description': """
This Module Allows to import data from the cbi format
The Interbank Corporate Banking (<http://www.cbi-org.eu>), the Italian CBI, is a telematic banking service allowing firms of all sizes to work directly, through their computer, with all the banks they have relations with.
The CBI standards, defined by the Consortium, are aimed at a comprehensive definition of Functions able to utterly satisfy Business requirements of both Enterprises and Banks
""",
    'author': 'omniaSolutions.website',
    'maintainer': 'omniaSolutions.website',
    'website': 'https://omniaSolutions.website',
    'depends': ['account_bank_statement_import'],
    'data': ['wizard/account_bank_statement_import_cbi.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
