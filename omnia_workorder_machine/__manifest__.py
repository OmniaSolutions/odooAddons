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
    'name': 'Omnia Workorder Machine',
    'version': '14.0',
    'author': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.eu',
    'category': 'report',
    'sequence': 15,
    'summary': 'Omnia Workorder Machine',
    'images': [],
    'depends': [
                'web',
                'web_editor',
                'mrp'],
    'description': """ This module allows to update workorder using a simple web interface.""",
    'data': [
        'views/templates_wo_simple.xml',
        'views/templates_by_user.xml',
        'views/mrp_workorder.xml',
        'views/mrp_workcenter.xml',
        'views/ir_config_parameter.xml',
        'views/template_workorder_machine_all.xml',
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
