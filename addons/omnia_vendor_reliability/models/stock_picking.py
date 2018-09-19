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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def getDateTime(self, strDateTime):
        return datetime.strptime(strDateTime, DEFAULT_SERVER_DATETIME_FORMAT)
        
    @api.multi
    @api.depends('date_done', 'scheduled_date')
    def _computeLeadDeliveryTime(self):
        for pickBrws in self:
            if not pickBrws.date_done or not pickBrws.scheduled_date:
                pickBrws.lead_delivery_time = 0
            else:
                datetime_done = self.getDateTime(pickBrws.date_done)
                datetime_scheduled = self.getDateTime(pickBrws.scheduled_date)
                delta_time = datetime_done - datetime_scheduled
                delay = 0.0
                delay += delta_time.days * 24
                delay += delta_time.seconds / float(60*60)
                pickBrws.lead_delivery_time = delay
            
    lead_delivery_time = fields.Float(_('Lead Delivery Time'), compute=_computeLeadDeliveryTime)

