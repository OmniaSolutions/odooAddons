'''
Created on 16 Jan 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder']
    task_id = fields.Many2one('project.task',
                              string=_('Reference Task'))

    user_id = fields.Many2one('res.users',
                              related='task_id.user_id',
                              string=_('Assigned User'))

    @api.multi
    def _getTotalTimeSpent(self):
        for workorder_id in self:
            workorder_id.user_time_spent = workorder_id.task_id.effective_hours
    user_time_spent = fields.Float(string=_('User Time Used'),
                                   compute=_getTotalTimeSpent)

    @api.multi
    def create_task(self):
        task_obj = self.env['project.task']
        for workorder_id in self:
            values = {'name': workorder_id.name,
                      'project_id': workorder_id.production_id.project_id.id,
                      'user_id': workorder_id.user_id.id,
                      'planned_hours': workorder_id.duration_expected
                      }
            task_id = task_obj.create(values)
            workorder_id.task_id = task_id.id
