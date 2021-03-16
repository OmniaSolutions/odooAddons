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
    'name': 'DocFly fatturapa Conservazione',
    'version': '10.0.1.1.0',
    'sequence': 1,
    'category': 'Custom',
    'description': """
DocFly aruba conservazione sostitutiva
======================================
Questo modulo permette di connettersi a servizio doc fly conservazione sostitutiva fornito da aruba e di conservare via ftp le fatture 
""",
    'author': 'OmniaSolutions.website',
    'maintainer': 'OmniaSolutions.website',
    'website': 'http://www.OmniaSolutions.website',
    'depends': ['document',
                'l10n_it_fatturapa',
                'l10n_it_fatturapa_out',
                'l10n_it_fatturapa_in'],
    'data': [
                #view
                'views/fattura_pa_export_conservation.xml',
                'views/fattura_pa_export_conservation_params.xml',
                'views/data.xml',
                'views/security.xml',
#              #report
#               'report/report_omnia_account_invoice.xml',
#              #menu
#                'menu_configuration.xml',
#              #security
#                'security/ddt_groups.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

