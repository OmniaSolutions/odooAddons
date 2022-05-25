'''
Created on 3 Sep 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class StockLocation(models.Model):
    _inherit = ['stock.location']

    @api.model
    def getSubcontractingLocation(self):
        for stock_location in self.search([('name', '=', 'Subcontracting')]):
            return stock_location
        return self.create({'usage': 'production',
                            'name': 'Subcontracting'})
