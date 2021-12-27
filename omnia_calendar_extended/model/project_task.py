'''
Created on 3 Apr 2017

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class ProjectTask(models.Model):
    '''
        extent the base class adding some new feature
    '''
    _inherit = ['project.task']
    
    event_ids = fields.One2many('calendar.event', 'task_id', 'Calendar event')
    