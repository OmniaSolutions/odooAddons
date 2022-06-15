'''
Created on 16 Jan 2018

@author: mboscolo
'''
import math
import logging
import datetime
from dateutil.relativedelta import relativedelta
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class externalProductionPartner(models.TransientModel):
    _name = 'external.production.partner'
    _description = 'Sub-Contracting External production partner'

    partner_id = fields.Many2one('res.partner',
                                 string=_('External Partner'),
                                 required=True)
    default = fields.Boolean(_('Default'))
    price = fields.Float('Price',
                         default=0.0,
                         digits='Product Price',
                         required=True,
                         help="The price to purchase a product")
    delay = fields.Integer('Delivery Lead Time',
                           default=1,
                           required=True,
                           help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
    min_qty = fields.Float('Minimal Quantity',
                           default=0.0,
                           required=True,
                           help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    wizard_id = fields.Many2one('mrp.production.externally.wizard',
                                string="Vendors")
    sequence = fields.Integer(string=_('Sequence'))

    def name_get(self):
        out = []
        for ext_partner in self:
            to_see = '%s | %s' % (ext_partner.partner_id.display_name, ext_partner.price)
            out.append((ext_partner.id, to_see))
        return out

    @api.onchange('subcontract_to')
    def change_subcontract_to(self):
        if self.subcontract_to.subcontract_to:
            self.subcontract_to = False


class externalWorkorderPartner(models.TransientModel):
    _name = 'external.workorder.partner'
    _description = 'Sub-Contractiong External Workorder Partner'
    
    partner_id = fields.Many2one('res.partner',
                                 string=_('External Partner'),
                                 required=True)
    default = fields.Boolean(_('Default'))
    price = fields.Float('Price',
                         default=0.0,
                         digits='Product Price',
                         required=True,
                         help="The price to purchase a product")
    delay = fields.Integer('Delivery Lead Time',
                           default=1,
                           required=True,
                           help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
    min_qty = fields.Float('Minimal Quantity',
                           default=0.0,
                           required=True,
                           help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    wizard_id = fields.Many2one('mrp.workorder.externally.wizard',
                                string="Vendors")

    def name_get(self):
        out = []
        for ext_partner in self:
            to_see = '%s | %s' % (ext_partner.partner_id.display_name, ext_partner.price)
            out.append((ext_partner.id, to_see))
        return out