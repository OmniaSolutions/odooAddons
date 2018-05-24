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
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
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

'''
Created on Dec 18, 2017

@author: daniel
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
import logging
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ['mrp.production']

    project_id = fields.Many2one('project.project',
                                 string=_('Project'),
                                 help=_('Project related to this production, if set the at action plan for each workorder a new task is created'))

    @api.multi
    def _total_progect_time(self):
        for production_id in self:
            total = 0.0
            for task_id in production_id.project_id.tasks:
                total = total + task_id.effective_hours
            production_id.totale_project_time = total
    totale_project_time = fields.Float(compute=_total_progect_time,
                                       string=_('Total time'),
                                       help=_('Total time spent on this manufacture'))

    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        for obj_prj in self:
            if obj_prj.project_id:
                for workorder_id in obj_prj.workorder_ids:
                    workorder_id.create_task()
        return res
