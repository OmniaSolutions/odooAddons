##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 10/lug/2013 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 10/lug/2013
@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _ 
import logging


class OmniaDdtAccountIvoice(models.Model):
    _inherit = ['account.invoice']
    is_accompagnatoria = fields.Boolean("Is Accompagnatoria")
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")
    delivery_address = fields.Many2one('res.partner', string='Delivery address')
    data_ritiro = fields.Datetime('Data e ora ritiro')
    data_consegna = fields.Datetime('Data e ora consegna')
    carriage_condition_id = fields.Many2one('stock.picking.carriage_condition', 'Carriage condition')
    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods')
    transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for transportation')
    ddt_reason = fields.Selection((('MITTENTE', 'Mittente'),
                                   ('DESTINATARIO', 'Destinatario'),
                                   ('VETTORE', 'Vettore'),
                                   ),
                                  'Trasporto a Cura di')
    peso_lordo = fields.Float(_('Peso Lordo'))
    peso_netto = fields.Float(_('Peso Netto'))
    volume = fields.Char('Volume', size=64)
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
    notes_invoice = fields.Char(string='Annotazioni')
    
    @api.multi
    def action_invoice_open(self):
        res = super(OmniaDdtAccountIvoice, self).action_invoice_open()
        for invoice_line in self.invoice_line_ids:
            msg = ""
            check_ord = []
            for sale_line in invoice_line.sale_line_ids:
                for procurament_id in sale_line.procurement_ids:
                    for move_id in procurament_id.move_ids:
                        pass
                        # todo: finire il giro della convalida dei move 
                        
                        #move_id.
                        #if move_id.picking_id and move_id.picking_id.ddt_number:
                        #    ddt_number = move_id.picking_id.ddt_number
                        #    if ddt_number not in check_ddt:
                        #        ddt_msg += " %s " % ddt_number
                        #        check_ddt.append(ddt_number)
        return res

    @api.onchange('partner_id')
    def onchange_partner(self):
        for invoice in self:
            final_address = False
            if invoice.partner_id:
                for child in invoice.partner_id.child_ids:
                    if child.type == 'delivery':
                        final_address = child.id
            invoice.delivery_address = final_address
                
                
            
            