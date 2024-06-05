'''
Created on 16 Jan 2018

@author: mboscolo
'''
import logging
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.exceptions import UserError


class WizProductReplace(models.TransientModel):
    _name = 'wiz.product.replace'
    _description = 'Wizard product replace'

    from_product_id = fields.Many2one('product.product',
                                      string="From Product")
    from_product_id_count = fields.Integer("Row Affected", compute="_compute_bom_line_affected")
    to_product_id = fields.Many2one('product.product',
                                      string="To Product")
    @api.depends("from_product_id")
    def _compute_bom_line_affected(self):
        for wiz_id in self:
            wiz_id.from_product_id_count = self.env['mrp.bom.line'].search_count([('product_id','=', wiz_id.from_product_id.id)])

    def replace_product(self):
        msg = f"Replate product {self.from_product_id.display_name} with {self.to_product_id.display_name}"
        for mrp_bom_line in self.env['mrp.bom.line'].search([('product_id','=', self.from_product_id.id)]):
            mrp_bom_line.product_id=self.to_product_id.id
            mrp_bom_line.bom_id.message_post(body=msg)
        
        
        
        
        