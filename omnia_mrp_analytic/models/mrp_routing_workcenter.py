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


class MrpRoutingWorkcenter(models.Model):
    _inherit = ['mrp.routing.workcenter']
    user_time_percentage = fields.Float("User Percentage to use of machine time", default=0.0)
