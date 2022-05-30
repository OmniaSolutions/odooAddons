'''
Created on 18 Mar 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.routing.workcenter'
    default_supplier = fields.Many2one('res.partner',
                                       string='Default Supplier')
    external_product = fields.Many2one('product.product',
                                       string=_('External Product use for external production'))