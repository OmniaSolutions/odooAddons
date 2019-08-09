'''
Created on 26 Apr 2018

@author: dsmerghetto
'''
import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    ir_attachment_relation = fields.Many2many(relation="mrp_routing_workcenter_ir_attachment",
                                              comodel_name='ir.attachment',
                                              column1="mrp_id",
                                              column2="attachemnt_id")
