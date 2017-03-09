# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2012 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#
#    Author : Smerghetto Daniel  (Omniasolutions)
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
from odoo import models
from odoo import fields
from odoo import api


class stock_picking_carriage_condition(models.Model):
    """
    Carriage condition
    """
    _name = "stock.picking.carriage_condition"
    _description = "Carriage Condition"
    name = fields.Char('Carriage Condition', size=64, required=True, readonly=False)
    note = fields.Text('Note')


class stock_picking_goods_description(models.Model):
    """
    Description of Goods
    """
    _name = 'stock.picking.goods_description'
    _description = "Description of Goods"

    name = fields.Char('Description of Goods', size=64, required=True, readonly=False)
    note = fields.Text('Note')


class stock_picking_reason(models.Model):
    """
    Reason for Transportation
    """
    _name = 'stock.picking.transportation_reason'
    _description = 'Reason for transportation'

    name = fields.Char('Reason For Transportation', size=64, required=True, readonly=False)
    note = fields.Text('Note')


class stock_picking_custom(models.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'
    carriage_condition_id = fields.Many2one('stock.picking.carriage_condition', 'Carriage condition')
    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods')
    transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for transportation')
    invoice_id = fields.Many2one('account.invoice', 'numberDDT', readonly=1)
    delivery_address = fields.Many2one('res.partner', "Indirizzo di spedizione secondario")
    ddt_number = fields.Char('DDT', size=64)
    volume = fields.Char('Volume', size=64)
    ddt_date = fields.Date('DDT date')
    actual_date = fields.Date('Data')
    note_ddt = fields.Text('Note')
    ddt_reason = fields.Selection((('MITTENTE', 'Mittente'),
                                   ('DESTINATARIO', 'Destinatario'),
                                   ('VETTORE', 'Vettore'),
                                   ),
                                  'Trasporto a Cura di')
    use_for_ddt = fields.Boolean('Use for DDT')

    @api.model
    def getLastDDtDate(self):
        """
            get last ddt date from all ddt
        """
        sql = """SELECT ddt_number,ddt_date FROM STOCK_PICKING WHERE DDT_NUMBER IS NOT NULL ORDER BY DDT_DATE DESC LIMIT 1;"""
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()
        failReturnDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
        for result in results:
            ddtDate = result.get('ddt_date', '2000-01-01')
            if not ddtDate:
                return failReturnDate
            return datetime.strptime(ddtDate, '%Y-%m-%d')
        return failReturnDate

    @api.multi
    def button_ddt_number(self, vals={}):
        lastDDtDate = self.getLastDDtDate()
        for brwsPick in self:
            if brwsPick.ddt_date is False:
                dateTest = datetime.now()
                brwsPick.write({'ddt_date': str(dateTest.strftime('%Y-%m-%d'))})
            else:
                dateTest = datetime.strptime(brwsPick.ddt_date, '%Y-%m-%d')
            if brwsPick.ddt_number is False or len(str(brwsPick.ddt_number)) == 0:
                if lastDDtDate > dateTest:
                    pass
                number = self.env.get('ir.sequence').next_by_code('stock.ddt')
                brwsPick.write({'ddt_number': number})
        return True

    # -----------------------------------------------------------------------------
    # EVITARE LA COPIA DI 'NUMERO DDT'
    # -----------------------------------------------------------------------------

    @api.multi
    def copy(self, default={}):
        default.update({'ddt_number': ''})
        return super(stock_picking_custom, self).copy(default)

stock_picking_custom()
