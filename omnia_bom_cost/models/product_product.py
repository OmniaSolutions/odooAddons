# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu)
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
#    All Right Reserved
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

'''
Created on Apr 17, 2018

@author: Matteo Boscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class ProductProduct(models.Model):
    _inherit = 'product.product'

    price_calc_skip = fields.Boolean(_('Skip Calc.'))

    def _set_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(product=self)
        if bom:
            boms_to_recompute = self.env['mrp.bom']
    
            if self.skipPriceCalculation():
                return
            else:
                for bom_line in bom.bom_line_ids:
                    bom_child = self.env['mrp.bom']._bom_find(product=bom_line.product_id)
                    if bom_child:
                        boms_to_recompute += bom_child 
                self.standard_price = self._compute_bom_price(bom, boms_to_recompute=boms_to_recompute)

    def _compute_bom_price(self, bom, boms_to_recompute=False):
        self.ensure_one()
        if self.skipPriceCalculation():
            return self.standard_price
        return super(ProductProduct, self)._compute_bom_price(bom, boms_to_recompute)

    def skipPriceCalculation(self):
        skip_calculation = False
        try:
            skip_calculation = eval(self.env['ir.config_parameter'].sudo().get_param('omnia_bom_cost.skip_product_cost_calc', 'False'))
        except Exception as ex:
            logging.warning(ex)
        return skip_calculation and self.skipProductCateg()

    def skipProductCateg(self):
        if self.price_calc_skip:
            return True
        return self.categ_id.price_calc_skip
