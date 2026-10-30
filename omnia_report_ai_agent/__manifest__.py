# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2026 https://OmniaSolutions.website
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
    'name': 'Omnia Report AI Agent',
    'version': '18.0.1.0.3',
    'author': 'OmniaSolutions',
    'license': 'LGPL-3',
    'website': 'http://www.omniasolutions.eu',
    'category': 'Omnia Customization',
    'sequence': 15,
    'summary': 'Generate AI-powered PDF reports directly from Server Actions.',
    'description': """
        AI Report Agent enables users to generate customized PDF reports
        using AI commands, instructions, and attachments directly from
        Server Actions.
    """,
    'depends': ['base', 'web', 'bus'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_agent_provider_account_data.xml',
        'views/res_config_settings_views.xml',
        'views/ir_actions_server_views.xml',
        'wizard/ai_report_agent_wizard_views.xml',
        'report/ai_report_agent_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
