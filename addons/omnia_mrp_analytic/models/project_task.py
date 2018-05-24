'''
Created on 24 May 2018

@author: mboscolo
'''


from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class Task(models.Model):
    _name = 'project.task'
    _inherit = ['project.task']

    user_time_percentage = fields.Float("User Percentage to use of machine time", default=0.0)
