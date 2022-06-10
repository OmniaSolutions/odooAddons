'''
Created on 16 Jan 2018

@author: mboscolo
'''
import math
import logging
import datetime
from dateutil.relativedelta import relativedelta
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class TmpStockMove(models.TransientModel):
    _name = "stock.tmp_move"
    _description = 'Sub-Contracting Template Move'

    name = fields.Char('Description', index=True, required=True)
    mrp_original_move = fields.Char(_('Is generated from origin MO'))
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('stock.move'),
        index=True, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], index=True, required=True,
        states={'done': [('readonly', True)]})
    product_uom_qty = fields.Float('Quantity',
                                   digits='Product Unit of Measure',
                                   default=1.0, required=True, states={'done': [('readonly', True)]},
                                   help="This is the quantity of products from an inventory "
                                        "point of view. For moves in the state 'done', this is the "
                                        "quantity of products that were actually moved. For other "
                                        "moves, this is the quantity of product that is planned to "
                                        "be moved. Lowering this quantity does not generate a "
                                        "back order. Changing this quantity on assigned moves affects "
                                        "the product reservation, and should be done with care.")
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
        help="Sets a location if you produce at a fixed location. This can be a partner location if you sub contract the manufacturing operations.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
        help="Location where the system will stock the finished products.")
    partner_id = fields.Many2one(
        'res.partner', 'Destination Address ',
        states={'done': [('readonly', True)]},
        help="Optional address where goods are to be delivered, specifically used for allotment")
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'),
        ('assigned', 'Available'), ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")
    origin = fields.Char("Source Document", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', help="Technical field depicting the warehouse to consider for the route selection on the next procurement (if any).")
    production_id = fields.Many2one(comodel_name='mrp.production', string='Production Id', readonly=True)
    #
    # production filed
    #
    external_prod_raw = fields.Many2one(comodel_name="mrp.production.externally.wizard",
                                        string="Raw",
                                        readonly=True)
    external_prod_finish = fields.Many2one(comodel_name="mrp.production.externally.wizard",
                                           string="Finished",
                                           readonly=True)
    #
    # work order field
    #
    external_prod_workorder_raw = fields.Many2one(comodel_name="mrp.workorder.externally.wizard",
                                                  string="Raw",
                                                  readonly=True)
    external_prod_workorder_finish = fields.Many2one(comodel_name="mrp.workorder.externally.wizard",
                                                     string="Finished",
                                                     readonly=True)
    scrapped = fields.Boolean('Scrapped', related='location_dest_id.scrap_location', readonly=True, store=True)
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]}, default=lambda self: self.env['uom.uom'].search([], limit=1, order='id'))
    date_expected = fields.Datetime('Scheduled date')
    workorder_id = fields.Many2one(comodel_name='mrp.workorder', string='Workorder Id', readonly=True)

    qty_available = fields.Float(_('Qty available'), compute='_compute_qty_available')
    location_available = fields.Many2one('stock.location', string=_('Qty Location'))
    mo_source_move = fields.Many2one('stock.move', string=_('Source MO stock move.'))


    @api.depends('location_dest_id', 'location_id')
    def _compute_qty_available(self):
        for move in self:
            move.qty_available = 0
            if move.product_id and move.location_dest_id:
                move.qty_available = move.checkQuantQty(move.product_id, move.location_dest_id)

    def checkQuantQty(self, product, location):
        stock_quant_model = self.env['stock.quant']
        stock_quants = stock_quant_model.search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
            ])
        for quant in stock_quants:
            return quant.quantity
        return 0

    @api.onchange('product_id')
    def changeProduct(self):
        if not self.name and self.product_id:
            if self.workorder_id:
                if self.workorder_id.production_id.product_id == self.product_id:
                    raise UserError('You cannot use finished product in the workorder external production. Produce externally the manufacturing order instead.')
            self.name = 'Subcontracting extra move %s' % (self.product_id.display_name)

    @api.onchange('partner_id')
    def changePartner(self):
        if self.partner_id:
            partner_location_id = self.external_prod_raw.getPartnerLocation(self.partner_id)
            if self.external_prod_raw:
                self.location_id = self.external_prod_raw.production_id.location_src_id.id
                self.location_dest_id = partner_location_id.id
            elif self.external_prod_finish:
                self.location_id = partner_location_id.id
                self.location_dest_id = self.external_prod_finish.production_id.location_src_id.id

    @api.model
    def create(self, vals):
        return super(TmpStockMove, self).create(vals)
