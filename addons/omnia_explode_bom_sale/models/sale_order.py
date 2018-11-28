'''
Created on Jun 3, 2016

@author: Daniel Smerghetto
'''

from odoo import models
from odoo import api
from odoo import _


class SaleOrderLineExtension(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def explode_bom(self):
        for saleLineBrws in self:
            order_id = saleLineBrws.order_id.id
            normalBOMs = saleLineBrws.product_id.bom_ids.filtered(lambda x: x.type == 'normal')
            for nBomBrws in normalBOMs:
                for bomLineBrws in nBomBrws.bom_line_ids:
                    self.copy({'product_id': bomLineBrws.product_id.id,
                               'product_uom_qty': bomLineBrws.product_qty,
                               'price_unit': 0,
                               'name': '[%s] %s' % (saleLineBrws.product_id.engineering_code, bomLineBrws.product_id.name),
                               'order_id': order_id,
                               })
                break
        return {
            'name': '',
            'res_id': order_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
                
            
