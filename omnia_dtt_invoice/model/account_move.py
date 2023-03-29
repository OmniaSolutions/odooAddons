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
    _inherit = ['account.move']
    is_accompagnatoria = fields.Boolean("Is Accompagnatoria")
    carrier_id = fields.Many2one("res.partner", string="Carrier")
    delivery_address_id = fields.Many2one('res.partner', string='Delivery address')
    data_ritiro = fields.Datetime('Data e ora ritiro')
    data_consegna = fields.Datetime('Data e ora consegna')
    carriage_condition_id = fields.Many2one('stock.picking.carriage_condition', 'Carriage condition')
    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods')
    transportation_reason_id = fields.Many2one('stock.picking.transportation_reason', 'Reason for transportation')
    ddt_reason = fields.Selection([('MITTENTE', 'Mittente'),
                                   ('DESTINATARIO', 'Destinatario'),
                                   ('VETTORE', 'Vettore'),
                                   ],
                                  'Trasporto a Cura di')
    peso_lordo = fields.Float(_('Peso Lordo'))
    peso_netto = fields.Float(_('Peso Netto'))
    unita_misura_peso = fields.Many2one('uom.uom', string="Unita' di misura")
    volume = fields.Char('Volume', size=64)
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
    notes_invoice = fields.Char(string='Annotazioni')
    weight_validity_message = fields.Html(compute='_compute_weight_validity')

    @api.depends('peso_lordo', 'peso_netto')
    @api.onchange('peso_lordo', 'peso_netto')
    def _compute_weight_validity(self):
        for invoice in self:
            msg = ''
            if len('%.2f' % invoice.peso_lordo) > 7:
                msg += 'Accompagnatoria gross weight cannot be exported in e-invoice because limit is 7 carachters<br>'
            if len('%.2f' % invoice.peso_netto) > 7:
                msg += 'Accompagnatoria net weight cannot be exported in e-invoice because limit is 7 carachters<br>'
            if msg:
                msg = '<div style="background-color:#ffaa00;">%s</div>' % (msg)
            invoice.weight_validity_message = msg

    def action_invoice_open(self):
        res = super(OmniaDdtAccountIvoice, self).action_invoice_open()
        for invoice_line in self.invoice_line_ids:
            msg = ""
            check_ord = []
            for sale_line in invoice_line.sale_line_ids:
                for procurament_id in sale_line.procurement_ids:
                    for move_id in procurament_id.move_ids:
                        pass
        return res

    @api.onchange('partner_id')
    def onchange_partner(self):
        for invoice in self:
            final_address = False
            if invoice.partner_id:
                for child in invoice.partner_id.child_ids:
                    if child.type == 'delivery':
                        final_address = child.id
            invoice.delivery_address_id = final_address
    
    @api.onchange('delivery_address_id')
    def onchange_delivery_address(self):
        for invoice in self:
            if invoice.delivery_address_id:
                invoice.delivery_address = ''
                if invoice.delivery_address_id.street:
                    invoice.delivery_address += ' ' + invoice.delivery_address_id.street
                if invoice.delivery_address_id.city:
                    invoice.delivery_address += ' ' + invoice.delivery_address_id.city
                if invoice.delivery_address_id.zip:
                    invoice.delivery_address += ' ' + invoice.delivery_address_id.zip
                if invoice.delivery_address_id.state_id:
                    invoice.delivery_address += ' ' + invoice.delivery_address_id.state_id.name
                if invoice.delivery_address_id.country_id:
                    invoice.delivery_address += ' ' + invoice.delivery_address_id.country_id.name
            else:
                return    
                
                
            