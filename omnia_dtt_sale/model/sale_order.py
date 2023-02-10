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


class SaleOrdet(models.Model):
    _inherit = ['sale.order']
    is_accompagnatoria = fields.Boolean("Is Accompagnatoria")
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")
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
            