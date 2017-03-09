# -*- coding: utf-8 -*-
##############################################################################
#
#
#    Author : Smerghetto Daniel (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu)
#    All Right Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from odoo.exceptions import UserError
from odoo import fields
from odoo import models
from odoo import _
from odoo import api
import logging


class Stock_picking(models.Model):
    _inherit = 'stock.picking'
    ddt_sequence = fields.Many2one('ir.sequence', string="DDT Sequence")

    @api.model
    def getLastDDtDate(self, sequence_id):
        """
            get last ddt date from all ddt
        """
        if sequence_id:
            sql = """SELECT ddt_number, ddt_date FROM STOCK_PICKING WHERE ddt_number IS NOT NULL AND ddt_sequence=%s ORDER BY DDT_DATE DESC LIMIT 1;""" % (sequence_id)
            self.env.cr.execute(sql)
            results = self.env.cr.dictfetchall()
            for result in results:
                return datetime.strptime(result.get('ddt_date', '2000-01-01'), '%Y-%m-%d')
            return datetime.strptime('2000-01-01', '%Y-%m-%d')
        raise UserError(_('No sequence is provided!'))

    @api.multi
    def button_ddt_number(self, vals):
        for brwsPick in self:
            brwseId = brwsPick.ddt_sequence.id
            if brwseId is None:
                sql = """SELECT id FROM IR_SEQUENCE WHERE CODE ='stock.ddt';"""
                self.env.cr.execute(sql)
                brwseId = self.env.cr.dictfetchall()[0]['id']
            lastDDtDate = self.getLastDDtDate(brwseId)
            if brwsPick.ddt_date is False:
                dateTest = datetime.now()
                brwsPick.write({'ddt_date': str(dateTest.strftime('%Y-%m-%d'))})
            else:
                dateTest = datetime.strptime(brwsPick.ddt_date, '%Y-%m-%d')
            if brwsPick.ddt_number is False or len(str(brwsPick.ddt_number)) == 0:
                if lastDDtDate > dateTest:
                    raise UserError(_("Impossibile staccare il ddt con data antecedente all'ultimo ddt"))
                if brwsPick.ddt_sequence:
                    code = brwsPick.ddt_sequence.code
                    number = self.env.get('ir.sequence').next_by_code(code)
                else:
                    number = self.env.get('ir.sequence').next_by_code('stock.ddt')
                brwsPick.write({'ddt_number': number})
        return True

Stock_picking()


class Stock_picking_out_omnia(models.Model):
    _inherit = "ir.sequence"
    use_for_ddt = fields.Boolean(string="Use for DDT")

Stock_picking_out_omnia()
