'''
Created on Sep 17, 2018

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _computeAverageLeadTime(self):
        pickingEnv = self.env['stock.picking']
        pickingTypes = self.env['stock.picking.type'].search('code', '=', 'incoming')
        for partnerBrws in self:
            amount = 0
            pickingBrwsList = pickingEnv.search([
                ('partner_id', '=', partnerBrws.id),
                ('picking_type_id', 'in', pickingTypes.ids)
                ])
            for pickingBrws in pickingBrwsList:
                amount += pickingBrws.lead_delivery_time
            
            amount = amount / len(pickingBrwsList)
            amount += amount.days * 24
            amount += amount.seconds / float(60*60)
            partnerBrws.average_lead_time = amount
        
    min_lead_time = fields.Float(_('Minimum lead time'))
    max_lead_time = fields.Float(_('Maximum lead time'))
    average_lead_time = fields.Float(_('Average lead time'), compute=_computeAverageLeadTime)
