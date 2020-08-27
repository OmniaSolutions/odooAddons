# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2019 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
#    $Id$
#
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
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class ImportWizard(models.TransientModel):
    _name = 'import.wizard'
    
    product = fields.Many2one('product.product', string=_('Product'))
    
    @api.model
    def calculateAnalyticCost(self,
                              product_id,
                              project_id):
        """
        Calculate the cost of the production based on product id and project assigned to the mo
        product_id: product.product obj
        project_id: project.project obj
        """
        if not product_id:
            raise UserError(_('[ERROR] Missing product'))
        computed = []

        def _calculateAnalyticCost(product_id,
                                   project_id):
            """
            Calculate the cost of the production based on product id and project assigned to the mo
            product_id: product.product obj
            project_id: project.project obj
            """
            tot_price = 0
            if product_id in computed:
                return 0
            computed.append(product_id)
            production_id = self.env['mrp.production'].search([('product_id', '=', product_id), ('project_id', '=', project_id), ('state', '=', 'done')])
            for production in production_id:
                for row in production.move_raw_ids:
                    if self.env['mrp.production'].search_count([('product_id', '=', row.product_id.id), ('project_id', '=', project_id)]) > 0:
                        children_amount = _calculateAnalyticCost(row.product_id.id, project_id)
                        tot_price += children_amount * row.product_uom_qty
                    else:
                        tot_price += row.price_unit * row.product_uom_qty
            return tot_price

        return _calculateAnalyticCost(product_id, project_id)
        
    @api.model
    def createCostOnAnalyticAccount(self,
                                    product_id,
                                    project_id,
                                    cost):
        """
        Write product cost to analytic account
        product_id: product.product obj
        project_id: project.project obj
        """
        product_name = self.env['product.product'].browse(product_id).display_name
        line_to_create = {'name': _('Automatic calculation of production cost [%s]') % (product_name),
                          'account_id': project_id,
                          'amount': cost,
                          'product_id': product_id}
        check_line_id = self.env['account.analytic.line'].search([('product_id', '=', product_id), ('account_id', '=', project_id)])
        if check_line_id:
            for line_id in check_line_id:
                line_id.write({'amount': cost})
        else:
            self.env['account.analytic.line'].create(line_to_create)
    
    @api.multi
    def import_data(self):
        product_id = self.product.id
        project_id = self.env.context.get('active_id')
        cost = self.calculateAnalyticCost(product_id,
                                          project_id)
        self.createCostOnAnalyticAccount(product_id,
                                         project_id,
                                         cost)
        vals = self.env.ref('analytic.account_analytic_line_action').read()[0]
        active_id = str(project_id)
        vals['domain'] = vals.get('domain', '').replace('active_id', active_id)
        vals['context'] = vals.get('context', '').replace('active_id', active_id)
        return vals
