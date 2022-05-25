# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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
    'name': 'Omnia Manufacturing Sub contracting Rule',
    'version': '14.0.1',
    'sequence': 1,
    'category': 'mrp',
    'description': """
Implements the sub contracting using the mrp order 
""",
    'author': 'OmniaSolutions.website',
    'maintainer': 'OmniaSolutions.website',
    'website': 'http://www.OmniaSolutions.website',
    'depends': ['stock',
                'delivery',
                'purchase',
                'mrp',
                'mrp_subcontracting',
                'l10n_it_fatturapa_in'
                ],
    'data': [# security
             'security/ir.model.access.csv',
             'security/secure.xml',
             #  wizard
             'wizard/wizard.xml',
             #  view
             'views/mrp_production.xml',
             'views/mrp_routing_workcenter.xml',
             'views/purchase.xml',
             'views/mrp_bom.xml',
             'views/res_partner.xml',
             'views/mrp_workorder.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
