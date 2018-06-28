# -*- coding: utf-8 -*-
# © 2016 OdooMRP team
# © 2016 AvanzOSC
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Eficent Business and IT Consulting Services, S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 OmniaSolutions S.N.C di Boscolo Matteo & C info@omniasolutions.eu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api
from odoo import models
from odoo import fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _is_out_of_request_date(self):
        outMsg = []
        for order in self:
            for line in order.order_line:
                if line.lineIsOutRequestDate():
                    outMsg.append("""<div style="background-color:red;font-size: 20px;color:white">Product <b>[%r]</b> in late</div><br/>""" % line.name)
            htmlBody = ""
            found = False
            for line in outMsg:
                htmlBody += line
                found = True
            if found:
                order.is_out_of_request_date = htmlBody
    is_out_of_request_date = fields.Html(string="Check if the move line request date is different from expected date",
                                         compute=_is_out_of_request_date)

    @api.multi
    @api.onchange('requested_date')
    def onchange_requested_date(self):
        """Warn if the requested dates is sooner than the commitment date"""
        result = super(SaleOrder, self).onchange_requested_date()
        if not result:
            result = {}
        if not self:
            return result
        self.ensure_one()
        if 'warning' not in result:
            lines = []
            for line in self.order_line:
                lines.append((1, line.id, {'requested_date':
                                           self.requested_date}))
            result['value'] = {'order_line': lines}
        return result
