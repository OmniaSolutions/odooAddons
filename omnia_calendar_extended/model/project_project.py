'''
Created on 3 Apr 2017

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class ProjectProject(models.Model):
    '''
        extent the base class adding some new feature
    '''
    _inherit = ['project.project']

    event_ids = fields.One2many('calendar.event', 'project_id', 'Calendar event')
    