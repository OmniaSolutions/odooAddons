'''
Created on 10 Apr 2017

@author: mboscolo
'''

from odoo import api, fields, models, _


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_quotation_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/quote/%s/%s?pdf=True' % (self.id, self.access_token)
        }

sale_order()
