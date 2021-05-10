'''
Created on Jun 3, 2016

@author: Daniel Smerghetto
'''

from odoo import models
from odoo import api
from odoo import _


class PurchaseOrderLineExtension(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def explode_bom(self):
        for lineBrws in self:
            order_id = lineBrws.order_id.id
            normalBOMs = lineBrws.product_id.bom_ids.filtered(lambda x: x.type == 'normal')
            for nBomBrws in normalBOMs:
                for bomLineBrws in nBomBrws.bom_line_ids:
                    self.copy({'product_id': bomLineBrws.product_id.id,
                               'product_qty': bomLineBrws.product_qty * lineBrws.product_qty,
                               'price_unit': bomLineBrws.product_id.standard_price,
                               'name': '[%s] %s' % (lineBrws.product_id.engineering_code, bomLineBrws.product_id.name),
                               'order_id': order_id,
                               })
                break
        return {
            'name': '',
            'res_id': order_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
                
            
