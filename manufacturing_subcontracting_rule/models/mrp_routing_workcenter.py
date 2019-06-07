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
from odoo.exceptions import UserError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    default_supplier = fields.Many2one('res.partner',
                                       string='Default Supplier')
    external_product = fields.Many2one('product.product',
                                       string=_('External Product use for external production'))

    external_operation = fields.Selection([('', ''),
                                           ('normal', 'Normal'),
                                           ('parent', 'Parent'),
                                           ('operation', 'Operation')],
                                           string=_('Produce it externally automatically as'),
                                           help="""Normal: Use the Parent object as Product for the Out Pickings and the raw material for the Out Picking
                                                   Parent: Use the Parent product for the In Out pickings
                                                   Operation: Use the Product that have the Operation assigned for the In Out pickings""")

    @api.model
    def create(self, vals):
        if vals.get('external_operation', '') == 'normal':
            routing = vals.get('routing_id', False)
            routing_id = self.env['mrp.routing'].browse(routing)
            for operation_id in routing_id.operation_ids:
                if operation_id.external_operation == 'normal':
                    raise UserError("You can set only one Normal operation for each routing")
        return super(MrpRoutingWorkcenter, self).create(vals)

