'''
Created on 3 Apr 2017

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class CalendaEvent(models.Model):
    '''
        extent the base class adding some new feature
    '''
    _inherit = ['calendar.event']

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project', domain=[('allow_timesheets', '=', True)])

    
