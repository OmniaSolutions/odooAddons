# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, models, fields
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_buy(self, procurements):
        """Create or update purchase orders based on a procurement record."""
        cache = {}
        for procurement, rule in procurements:
            product_id = procurement.product_id
            product_qty = procurement.product_qty
            product_uom = procurement.product_uom
            location_id = procurement.location_id
            name = procurement.name
            origin = procurement.origin
            values = procurement.values.copy() if hasattr(procurement, 'values') else {}

            suppliers = product_id.seller_ids.filtered(
                lambda r: (not r.company_id or r.company_id == values['company_id']) and
                          (not r.product_id or r.product_id == product_id)
            )

            if not suppliers:
                msg = _(
                    'There is no vendor associated to the product %s. Please define a vendor for this product.') % product_id.display_name
                raise UserError(msg)

            supplier = suppliers[0]
            partner = supplier.partner_id
            values['supplier'] = supplier
            company_id = procurement.values.get('company_id') or self.env.user.company_id
            domain = rule._make_po_get_domain(company_id, values, partner)
            if domain in cache:
                po = cache[domain]
            else:
                po = self.env['purchase.order'].sudo().search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po

            if not po:
                company_id = procurement.company_id or self.env.user.company_id
                origins = [procurement.origin]
                supplierinfo = product_id.seller_ids[:1]

                values = [{
                    'date_planned': fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'product_id': product_id.id,
                    'product_qty': product_qty,
                    'product_uom': product_id.uom_id.id,
                    'supplier': supplierinfo,
                    'partner_id': supplierinfo.partner_id.id if supplierinfo else False,
                    'analytic_distribution': procurement.values.get('analytic_distribution'),
                    'move_dest_ids': procurement.values.get('move_dest_ids'),
                }]

                vals = self._prepare_purchase_order(
                    company_id,
                    origins,
                    values
                )

                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'incoming'),
                    ('company_id', '=', company_id.id),
                ], limit=1)

                if not picking_type:
                    raise UserError(_("No incoming picking type found for company %s") % company_id.name)

                vals['picking_type_id'] = picking_type.id
                po = self.env['purchase.order'].with_company(company_id).sudo().create(vals)
                cache[domain] = po

            elif not po.origin or origin not in (po.origin or '').split(', '):

                po.write({'origin': ', '.join(filter(None, [po.origin, origin]))})

            # MERGE OR CREATE PO LINE
            po_line_merged = False
            analytic_id = self.env.context.get('omnia_analytic_id')
            for line in po.order_line:
                if (line.product_id == product_id and
                        line.product_uom == product_id.uom_po_id and
                        analytic_id and str(analytic_id) in (line.analytic_distribution or {})):  # analytic match
                    if line._merge_in_existing_line(
                            product_id, product_qty, product_uom, location_id, name, origin, values):
                        vals_line = self._update_purchase_order_line(
                            product_id, product_qty, product_uom, values, line, partner)
                        line.write(vals_line)
                        po_line_merged = True
                        break

            if not po_line_merged:
                vals_line = self._prepare_purchase_order_line(
                    product_id, product_qty, product_uom, values, po, partner
                )
                self.env['purchase.order.line'].sudo().create(vals_line)

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, partner):
        """
        Prepare a purchase order line, carrying the analytic_distribution from the procurement context
        """

        supplier = values[0]['supplier'] if isinstance(values, list) else values.get('supplier')
        company_id = po.company_id

        base_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
            product_id,
            product_qty,
            product_uom,
            company_id,
            supplier,
            po
        )

        analytic_distribution = (values[0].get('analytic_distribution') if isinstance(values, list)
                                 else values.get('analytic_distribution'))
        if not analytic_distribution:
            analytic_id = self.env.context.get('omnia_analytic_id')
            if analytic_id:
                analytic_distribution = {str(analytic_id): 100}
        if analytic_distribution:
            base_vals['analytic_distribution'] = analytic_distribution

        move_dest = values[0].get('move_dest_ids') if isinstance(values, list) else values.get('move_dest_ids')
        if move_dest:
            if isinstance(move_dest, list):
                for _, move_id in move_dest:
                    base_vals['omnia_mrp_orig_move'] = move_id
                    break
            else:
                base_vals['omnia_mrp_orig_move'] = move_dest.id

        return base_vals

    def _get_purchase_order_date(self, product_id, product_qty, product_uom, values, partner, schedule_date):
        """Return the datetime value to use as Order Date (``date_order``) for the
           Purchase Order created to satisfy the given procurement. """
        purchase_date = super(StockRule, self)._get_purchase_order_date(product_id, product_qty, product_uom, values, partner, schedule_date)
        if purchase_date < fields.Datetime.now():
            return fields.Datetime.now()
        return purchase_date
