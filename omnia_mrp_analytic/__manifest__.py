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
    'name': 'Omnia Mrp Analytics',
    'version': '1.1',
    'sequence': 1,
    'category': 'Custom',
    'description': """
Add analytics fields to the production order and create task for each work order in order to compute the time spend task and production
""",
    'author': 'OmniaSolutions.eu',
    'maintainer': 'OmniaSolutions.eu',
    'website': 'http://www.OmniaSolutions.eu',
    'depends': ['mrp',
                'project',
                'hr_timesheet'],
    'data': [
        #  view
        'views/mrp_production.xml',
        'views/mrp_workorder.xml',
        'views/mrp_routing_workcenter.xml',
        'views/project_task.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
