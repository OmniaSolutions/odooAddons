'''
Created on 18 Jul 2018

@author: mboscolo
'''
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import math
import logging


class ChangeProductionQty(models.TransientModel):
    _inherit = "change.production.qty"

    # @api.multi
    def change_prod_qty_external(self, productionBrws):
        raise UserError(_('You cannot change manufacturing order quantity if you are producing it externally. Cancel the external production and update the quantity.'))

    # @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            if production.state == 'external':
                self.change_prod_qty_external(production)
            else:
                super(ChangeProductionQty, self).change_prod_qty()
