# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from odoo import models
from odoo import fields
from odoo import api
from odoo import _


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    starting_date = fields.Datetime(_('Starting Date'))
    ending_date = fields.Datetime(_('Ending Date'))

    def convertToDateTime(self, strDate):
        return fields.Datetime.from_string(strDate)

    @api.onchange('ending_date')
    def endingDatechanged(self):
        if self.starting_date:
            endingDate = self.convertToDateTime(self.ending_date)
            startingDate = self.convertToDateTime(self.starting_date)
            if startingDate < endingDate:
                delta = self.convertToDateTime(self.ending_date) - self.convertToDateTime(self.starting_date)
                seconds = delta.seconds
                minute, seconds = divmod(seconds, 60)
                hours, minute = divmod(minute, 60)
                self.unit_amount = int(hours) + self.toDecimal(minute)

    def toDecimal(self, sexa):
        return sexa / 60.0

    @api.onchange('starting_date')
    def startingDatechanged(self):
        if self.starting_date:
            self.date = self.convertToDateTime(self.starting_date).date()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
