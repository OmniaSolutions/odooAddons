'''
Created on Sep 17, 2018

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
import numpy
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _compute_color(self):
        for partnerBrws in self:
            stdMsg = '<div style="border: 2px solid %s;text-align: center;"><div style="color:%s; font-weight:bold;">%s</div></div>'
            color = '#ffc202'
            msg = _('Normal delivery')
            if partnerBrws.average_lead_time <= partnerBrws.min_lead_time:
                color = '#68c30f'
                msg = _('Reliable delivery')
            elif partnerBrws.average_lead_time >= partnerBrws.max_lead_time:
                color = '#db2c00'
                msg = _('Unreliable delivery')
            partnerBrws.delay_color = stdMsg % (color, color, msg)
        
    @api.multi
    def _computeAverageLeadTime(self):
        pickingEnv = self.env['stock.picking']
        pickingTypes = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
        for partnerBrws in self:
            amount = 0
            pickingBrwsList = pickingEnv.search([
                ('partner_id', '=', partnerBrws.id),
                ('picking_type_id', 'in', pickingTypes.ids)
                ])
            deliveryDelayList = [pickingBrws.lead_delivery_time for pickingBrws in pickingBrwsList]
            if deliveryDelayList:
                amount = numpy.average(deliveryDelayList)
            partnerBrws.average_lead_time = amount
        
    min_lead_time = fields.Float(_('Minimum lead time'))
    max_lead_time = fields.Float(_('Maximum lead time'))
    average_lead_time = fields.Float(_('Average lead time'), compute=_computeAverageLeadTime)
    delay_color = fields.Html(string='', compute=_compute_color, readonly=True)
