# -*- coding: utf-8 -*-
# © 2016 OdooMRP team
# © 2016 AvanzOSC
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Eficent Business and IT Consulting Services, S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 OmniaSolutions S.N.C di Boscolo Matteo & C info@omniasolutions.eu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api
from odoo import fields
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    requested_date = fields.Datetime()

    @api.multi
    def write(self, vals):
        for line in self:
            if not line.requested_date and line.order_id.requested_date and\
                    'requested_date' not in vals:
                vals.update({
                    'requested_date': line.order_id.requested_date
                })
        return super(SaleOrderLine, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.order_id.requested_date and not res.requested_date:
            res.write({'requested_date': res.order_id.requested_date})
        return res

    @api.model
    def lineIsOutRequestDate(self):
        for stock_move in self.env['stock.move'].search([('sale_line_id', '=', self.id)]):
            if stock_move.requested_date and stock_move.date_expected:
                rDate = datetime.strptime(stock_move.requested_date, DEFAULT_SERVER_DATETIME_FORMAT)
                aDate = datetime.strptime(stock_move.date_expected, DEFAULT_SERVER_DATETIME_FORMAT)
                if rDate < aDate:
                    return True
        return False
