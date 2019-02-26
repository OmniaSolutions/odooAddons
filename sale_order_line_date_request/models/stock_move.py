# -*- coding: utf-8 -*-
# Copyright 2018 OmniaSolutions S.N.C di Boscolo Matteo & C info@omniasolutions.eu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
'''
Created on 29 Mar 2018

@author: mboscolo
'''
from odoo import api
from odoo import fields
from odoo import models


class SaleMove(models.Model):
    _inherit = 'stock.move'
    #
    requested_date = fields.Datetime(string="Customer Request",
                                     related="sale_line_id.requested_date")
