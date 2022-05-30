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

    operation_type = fields.Selection([
        ('deliver', _('Deliver')),
        ('consume', _('Consume')),
        ('deliver_consume', _('Deliver and Consume')),
        ],
        default='deliver_consume',
        help="""
Deliver:   Send to subcontractor location
Stock -> Subcontractor

Consume:   Consume from subcontractor location
Subcontractor -> Subcontract location

Deliver and Consume:  Send to subcontractor location + Consume from subcontractor location
Stock -> Subcontractor
Subcontractor -> Subcontract location
        """
    )
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


class externalProductionPartner(models.TransientModel):
    _name = 'external.production.partner'
    _description = 'Sub-Contracting External production partner'

    partner_id = fields.Many2one('res.partner',
                                 string=_('External Partner'),
                                 required=True)
    default = fields.Boolean(_('Default'))
    price = fields.Float('Price',
                         default=0.0,
                         digits='Product Price',
                         required=True,
                         help="The price to purchase a product")
    delay = fields.Integer('Delivery Lead Time',
                           default=1,
                           required=True,
                           help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
    min_qty = fields.Float('Minimal Quantity',
                           default=0.0,
                           required=True,
                           help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    wizard_id = fields.Many2one('mrp.production.externally.wizard',
                                string="Vendors")


class MrpProductionWizard(models.TransientModel):

    _name = "mrp.production.externally.wizard"
    _description = 'Sub-Contracting Mrp Production Externally Wizard'

    external_partner = fields.One2many('external.production.partner',
                                       inverse_name='wizard_id',
                                       string=_('External Partner'))
    move_raw_ids = fields.One2many('stock.tmp_move',
                                   string=_('Raw Materials'),
                                   inverse_name='external_prod_raw',
                                   domain=[('scrapped', '=', False)])
    move_finished_ids = fields.One2many('stock.tmp_move',
                                        string=_('Finished Products'),
                                        inverse_name='external_prod_finish',
                                        domain=[('scrapped', '=', False)])
    operation_type = fields.Selection(selection=[('normal', _('Normal')), ('consume', _('Consume'))],
                                      string=_('Operation'),
                                      default='normal')
    consume_bom_id = fields.Many2one(comodel_name='mrp.bom',
                                     string=_('BOM To Consume'))
    production_id = fields.Many2one('mrp.production',
                                    string=_('Production'),
                                    readonly=True)
    workorder_id = fields.Many2one('mrp.workorder',
                                   string=_('WorkOrder'),
                                   readonly=True)
    request_date = fields.Datetime(string=_("Request date for the product"),
                                   default=lambda self: fields.datetime.now())
    create_purchese_order = fields.Boolean(_('Automatic create Purchase'), default=True)
    merge_purchese_order = fields.Boolean(_('Merge Purchase'), default=True)
    confirm_purchese_order = fields.Boolean(_('Confirm Purchase'), default=True)
    
    service_product_to_buy = fields.Many2one('product.product',
                                             string=_('Service Product to buy'),
                                             compute='_service_product',
                                             )
    service_prod_type = fields.Selection(related='service_product_to_buy.type', string=_('Service Product Type'))

    @api.model
    def _service_product(self):
        self.service_product_to_buy = self.getDefaultProductionServiceProduct()

    @api.onchange('external_partner')
    def changeExternalPartner(self, external_partner_model='external.production.partner'):
        active_partners = self.env['res.partner']
        ext_partners = self.env[external_partner_model]
        for partner_suppl_info in self.external_partner:
            ext_partners += partner_suppl_info
            partner_id = partner_suppl_info.partner_id
            active_partners += partner_id
            partner_location_id = self.getPartnerLocation(partner_id)
            if len(self.external_partner) == 1:
                for move_raw in self.move_raw_ids:
                    move_raw.location_dest_id = partner_location_id
                    move_raw.location_id = self.production_id.location_src_id
                    if not move_raw.partner_id:
                        move_raw.partner_id = partner_id.id
                for finish_move in self.move_finished_ids:
                    finish_move.location_dest_id = self.production_id.location_src_id
                    finish_move.location_id = partner_location_id
                    if not finish_move.partner_id:
                        finish_move.partner_id = partner_id.id
            else:
                existing_raw_moves = self.move_raw_ids.filtered(lambda x:x.partner_id.id == partner_id.id)
                if not existing_raw_moves:
                    partner_ids = self.move_raw_ids.mapped('partner_id')
                    if not partner_ids:
                        for move_raw in self.move_raw_ids:
                            move_raw.location_dest_id = partner_location_id
                            move_raw.location_id = self.production_id.location_src_id
                            move_raw.partner_id = partner_id.id
                        for finish_move in self.move_finished_ids:
                            finish_move.location_dest_id = self.production_id.location_src_id
                            finish_move.location_id = partner_location_id
                            finish_move.partner_id = partner_id.id
                    for partner in partner_ids:
                        if partner != partner_id:
                            for move_raw in self.move_raw_ids.filtered(lambda x:x.partner_id.id == partner.id):
                                new_raw_move = move_raw.copy()
                                new_raw_move.location_dest_id = partner_location_id
                                new_raw_move.location_id = self.production_id.location_src_id
                                new_raw_move.partner_id = partner_id.id
                            for finish_move in self.move_finished_ids.filtered(lambda x:x.partner_id.id == partner.id):
                                new_finish_move = finish_move.copy()
                                new_finish_move.location_dest_id = self.production_id.location_src_id
                                new_finish_move.location_id = partner_location_id
                                new_finish_move.partner_id = partner_id.id
                        break
        if active_partners:
            for line in self.move_raw_ids:
                if line.partner_id not in active_partners:
                    line.unlink()
            for line in self.move_finished_ids:
                if line.partner_id not in active_partners:
                    line.unlink()
        self.external_partner = ext_partners

    @api.onchange('request_date')
    def _request_date(self):
        for move in self.move_raw_ids:
            product_delay = move.product_id.produce_delay
            move.date_expected = fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
        for move in self.move_finished_ids:
            move.date_expected = self.request_date

    @api.onchange('consume_bom_id')
    def changeBOMId(self):
        self.operationTypeChanged()

    def getWizardBrws(self):
        return self.browse(self._context.get('wizard_id', False))

    @api.onchange('operation_type')
    def operationTypeChanged(self):
        pass
    
    def getParentObjectBrowse(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def cancelProductionRows(self, prodObj):
        for lineBrws in prodObj.move_raw_ids + prodObj.move_finished_ids:
            lineBrws.mrp_original_move = lineBrws.state
            lineBrws._action_cancel()

    def updateMoLinesWithNew(self, productionBrws):
        '''
            Update MO with new stock moves
        '''
        move_raw_ids = []
        move_finished_ids = []
        productsToCheck = []
        for external_partner in self.external_partner:
            for lineBrws in self.move_finished_ids:
                productsToCheck.append(lineBrws.product_id.id)
                vals = {'name': lineBrws.name,
                        'company_id': lineBrws.company_id.id,
                        'product_id': lineBrws.product_id.id,
                        'product_uom_qty': lineBrws.product_uom_qty,
                        'location_id': lineBrws.location_id.id,
                        'location_dest_id': lineBrws.location_dest_id.id,
                        'partner_id': external_partner.partner_id.id,
                        'note': lineBrws.note,
                        'state': 'confirmed',
                        'origin': lineBrws.origin,
                        'warehouse_id': lineBrws.warehouse_id.id,
                        'production_id': productionBrws.id,
                        'product_uom': lineBrws.product_uom.id,
                        'forecast_expected_date': fields.Datetime.from_string(self.request_date),
                        'mrp_production_id': productionBrws.id,
                        }
                move_finished_ids.append((0, False, vals))
            product_delay = external_partner.delay
            for lineBrws in self.move_raw_ids:
                productsToCheck.append(lineBrws.product_id.id)
                vals = {
                    'name': lineBrws.name,
                    'company_id': lineBrws.company_id.id,
                    'product_id': lineBrws.product_id.id,
                    'product_uom_qty': lineBrws.product_uom_qty,
                    'location_id': lineBrws.location_id.id,
                    'location_dest_id': lineBrws.location_dest_id.id,
                    'partner_id': external_partner.partner_id.id,
                    'note': lineBrws.note,
                    'state': 'confirmed',
                    'origin': lineBrws.origin,
                    'warehouse_id': lineBrws.warehouse_id.id,
                    'production_id': False,
                    'product_uom': lineBrws.product_uom.id,
                    'forecast_expected_date': fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0),
                    'mrp_production_id': productionBrws.id,
                }
                move_raw_ids.append((0, False, vals))
        productionBrws.write({'move_raw_ids': move_raw_ids,
                              'move_finished_ids': move_finished_ids,
                              'state': 'external',
                              'external_partner': (6, 0, [external_partner.partner_id.id])
                              })
        productsToCheck = list(set(productsToCheck))
        for product in self.env['product.product'].browse(productsToCheck):
            productionBrws.checkCreateReorderRule(product, productionBrws.location_src_id.get_warehouse())

    
    def getWorkorderAndManufaturing(self):
        productionBrws = self.env['mrp.production']
        objBrws = self.getParentObjectBrowse()
        workorderBrw = self.env['mrp.workorder']
        if objBrws._name == 'mrp.workorder':
            productionBrws = objBrws.production_id
            workorderBrw = objBrws
        else:
            productionBrws = objBrws
        return productionBrws, workorderBrw

    
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No external partner set. Please provide one !!"))
        if not self.create_purchese_order and len(self.external_partner.ids) != 1:
            raise UserError(_("If you don't want to create purchase order you have to select only one partner."))

        productionBrws, _workorderBrw = self.getWorkorderAndManufaturing()
        self.cancelProductionRows(productionBrws)
        self.updateMoLinesWithNew(productionBrws) # Update MO with new stock moves
        date_planned_finished = False
        date_planned_start = False
        pickingBrwsList = []
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            pickOut = self.createStockPickingOut(partner_id, productionBrws)
            pickIn = self.createStockPickingIn(partner_id, productionBrws)
            pickingBrwsList.extend((pickIn.id, pickOut.id))
            date_planned_finished = pickIn.scheduled_date
            date_planned_start = pickOut.scheduled_date
            _po_created = self.createPurchase(external_partner, pickIn)
        productionBrws.state = 'draft'
        productionBrws.date_planned_finished = date_planned_finished
        productionBrws.date_planned_start = date_planned_start
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        movesToCancel = productionBrws.move_raw_ids.filtered(lambda m: m.mrp_original_move is False)
        movesToCancel2 = productionBrws.move_finished_ids.filtered(lambda m: m.mrp_original_move is False)
        movesToCancel += movesToCancel2
        movesToCancel._do_unreserve()
        movesToCancel._action_cancel()
        productionBrws.state = 'external'

    def getPurchaseVals(self, external_partner):
        return {'partner_id': external_partner.partner_id.id,
                'date_planned': self.request_date,
                'production_external_id': self.production_id.id,
                'workorder_external_id': False,
                }

    def getPurchaseLineVals(self, product, purchase, move_line):
        return {'product_id': product.id,
                'name': self.getPurcheseName(product),
                'product_qty': move_line.product_uom_qty,
                'product_uom': product.uom_po_id.id,
                'price_unit': product.price,
                'date_planned': self.request_date,
                'order_id': purchase.id,
                'production_external_id': self.production_id.id,
                'workorder_external_id': False,
                'sub_move_line': move_line.id,
                }

    def createPurchase(self, external_partner, picking):
        if not self.create_purchese_order:
            return 
        obj_product_product = self.getDefaultProductionServiceProduct()
        purchase_vals = self.getPurchaseVals(external_partner)
        obj_po = self.env['purchase.order'].create(purchase_vals)
        for lineBrws in picking.move_lines:
            self.setupSupplierinfo(obj_product_product)
            values = self.getPurchaseLineVals(obj_product_product, obj_po, lineBrws)
            new_purchase_order_line = self.env['purchase.order.line'].create(values)
            new_purchase_order_line.onchange_product_id()
            new_purchase_order_line.date_planned = self.request_date
            new_purchase_order_line.product_qty = lineBrws.product_uom_qty
            lineBrws.purchase_order_line_subcontracting_id = new_purchase_order_line.id
            lineBrws.purchase_line_id = new_purchase_order_line
        if self.confirm_purchese_order:
            obj_po.button_confirm()
        return obj_po

    def setupSupplierinfo(self, product):
        supplierinfo = self.env['product.supplierinfo']
        for partner_tmp in self.external_partner:
            partner = partner_tmp.partner_id
            if partner_tmp.price > 0:
                supplierinfo_ids = supplierinfo.search([
                    ('name', '=', partner.id),
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('price', '=', partner_tmp.price),
                    ('delay', '=', partner_tmp.delay),
                    ('min_qty', '=', partner_tmp.min_qty)
                    ])
                if not supplierinfo_ids:
                    supplierinfo.create({
                        'name': partner.id,
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'price': partner_tmp.price,
                        'delay': partner_tmp.delay,
                        'min_qty': partner_tmp.min_qty
                        })
    
    @api.model
    def getNewExternalProductInfo(self):
        """
        this method could be overloaded as per customer needs
        """
        default_code = self.production_id.product_id.name
        if self.production_id.product_id.default_code:
            default_code = self.production_id.product_id.default_code
        new_default_code = "S-" + default_code
        new_name = "S-" + self.production_id.product_id.name
        val = {'default_code': new_default_code,
               'type': 'service',
               'purchase_ok': True,
               'name': new_name}
        return val

    @api.model
    def getDefaultProductionServiceProduct(self):
        """
        get the default external product suitable for the purchase
        """
        bom_product_product_id = self.production_id.bom_id.external_product
        if not bom_product_product_id:
            product_vals = self.getNewExternalProductInfo()
            bom_product_product_id = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
            if not bom_product_product_id:
                bom_product_product_id = self.env['product.product'].create(product_vals)
                bom_product_product_id.type = 'service'
                bom_product_product_id.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                        message_type='notification')
            self.production_id.bom_id.external_product = bom_product_product_id
        return bom_product_product_id

    @api.model
    def getPurcheseName(self, product_product):
        """
        this method could be overloaded as per customer needs
        """
        if product_product.default_code:
            return product_product.default_code + " - " + product_product.name
        else:
            return product_product.name

    
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()

    def getOrigin(self, productionBrws):
        return productionBrws.name

    def getIncomingTmpMoves(self, customerProductionLocation, partner_id, isWorkorder=False):
        incomingMoves = self.env['stock.tmp_move']
        lines = self.move_finished_ids
        if isWorkorder:
            lines = self.move_finished_ids
        for productionLineBrws in lines:
            if not customerProductionLocation:
                customerProductionLocation = productionLineBrws.location_id
            if productionLineBrws.state not in ['done', 'cancel']:  # and productionLineBrws.partner_id == partner_id:
                incomingMoves += productionLineBrws
        return incomingMoves.filtered(lambda x: x.partner_id.id == partner_id.id)

    def createStockPickingIn(self, partner_id, mrp_production_id, cancel_source_moves=True):
        stock_piking = self.env['stock.picking']
        if not self.move_finished_ids:
            return stock_piking
        customerProductionLocation = self.getPartnerLocation(partner_id)
        localStockLocation = mrp_production_id.location_src_id  # Taken from manufacturing order
        incomingMoves = self.getIncomingTmpMoves(customerProductionLocation, partner_id)
        toCreate = self.getPickingVals(partner_id, mrp_production_id, 'incoming')
        out_stock_picking_id = stock_piking.create(toCreate)
        for stock_move_id in incomingMoves:
            stock_move_vals = self.getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, customerProductionLocation, localStockLocation)
            self.env['stock.move'].create(stock_move_vals)
            if cancel_source_moves:
                mrp_production_id.move_finished_ids._action_cancel()
        mrp_production_id.createStockMoveBom()
        return out_stock_picking_id

    def getPickingType(self, mrp_production_id, picking_type):
        '''
            picking_type: 'incoming' | 'outgoing'
        '''
        warehouseId = mrp_production_id.picking_type_id.warehouse_id.id
        stock_picking_type = self.env['stock.picking.type']
        for stock_picking_type_id in stock_picking_type.search([('code', '=', picking_type),
                                                                ('active', '=', True),
                                                                ('warehouse_id', '=', warehouseId)]):
            return stock_picking_type_id.id
        return False

    def getPartnerLocation(self, partner_id):
        customerProductionLocation = partner_id.location_id
        if not customerProductionLocation:
            raise UserError(_('Partner %s has not location setup.' % (partner_id.name)))
        return customerProductionLocation

    def getSubcontractingLocation(self):
        ret = self.env['stock.location'].getSubcontractingLocation()
        if not ret:
            raise UserError(_('Cannot get subcontracting location %s.' % (ret)))
        return ret

    def getPickingVals(self, partner_id, mrp_production_id, operation_type):
        subcontract_loc = self.getSubcontractingLocation()
        if operation_type == 'outgoing':
            location_dest_id = self.getPartnerLocation(partner_id)
            location_id = mrp_production_id.location_src_id
            sub_contracting_operation = 'close'
        elif operation_type == 'incoming':
            location_dest_id = mrp_production_id.location_src_id
            location_id = self.getPartnerLocation(partner_id)
            sub_contracting_operation = 'open'
        elif operation_type == 'subcontracting_out':
            operation_type = 'outgoing'
            location_dest_id = subcontract_loc
            location_id = self.getPartnerLocation(partner_id)
            sub_contracting_operation = 'close'
        elif operation_type == 'subcontracting_in':
            operation_type = 'incoming'
            location_dest_id = self.getPartnerLocation(partner_id)
            location_id = subcontract_loc
            sub_contracting_operation = 'close'
        vals = {
            'partner_id': partner_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'move_type': 'direct',
            'picking_type_id': self.getPickingType(mrp_production_id, operation_type),
            'origin': self.getOrigin(mrp_production_id),
            'move_lines': [],
            'state': 'draft',
            'sub_contracting_operation': sub_contracting_operation,
            'sub_production_id': self.production_id.id,
            }
        return vals

    def getStockMoveVals(self, stock_move_id, mrp_production_id, out_stock_picking_id, location_id, location_dest_id):
        vals = {'name': stock_move_id.product_id.display_name,
                'production_id': False,
                'mrp_workorder_id': False,
                'mrp_production_id': mrp_production_id.id,
                'raw_material_production_id': False,
                'picking_id': out_stock_picking_id.id,
                'product_uom': stock_move_id.product_uom.id,
                'location_id': location_id.id,#stock_move_id.location_id.id,
                'location_dest_id': location_dest_id.id,#stock_move_id.location_dest_id.id,
                'sale_line_id': stock_move_id.mo_source_move.sale_line_id.id,
                'operation_type': stock_move_id.operation_type,
                'product_id': stock_move_id.product_id.id,
                'product_uom_qty': stock_move_id.product_uom_qty,
                'company_id': stock_move_id.company_id.id,
                'note': stock_move_id.note,
                'origin': stock_move_id.origin,
                'warehouse_id': stock_move_id.warehouse_id.id,
                'date_deadline': stock_move_id.date_expected,
                'mrp_original_move': False,
                'workorder_id': False,
                }
        return vals

    def createStockPickingOut(self, partner_id, mrp_production_id, cancel_source_moves=True):
        stock_picking = self.env['stock.picking']
        if not self.move_raw_ids or not self.move_raw_ids.filtered(lambda x: x.product_uom_qty > 0):
            return stock_picking
        customerProductionLocation = self.getPartnerLocation(partner_id)
        stock_location_id = mrp_production_id.location_src_id
        stock_move_ids = self.move_raw_ids
        out_stock_move_ids = stock_move_ids.filtered(lambda x: x.state not in ['done', 'cancel'])
        picking_vals = self.getPickingVals(partner_id, mrp_production_id, 'outgoing')
        out_stock_picking_id = stock_picking.create(picking_vals)
        for stock_move_id in out_stock_move_ids.filtered(lambda x: x.partner_id.id == partner_id.id):
            new_stock_move_id = self.env['stock.move']
            if stock_move_id.operation_type in ['deliver', 'deliver_consume']: # Create picking Stock -> Partner Location
                stock_move_vals = self.getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, stock_location_id, customerProductionLocation)
                new_stock_move_id = new_stock_move_id.create(stock_move_vals)
            if stock_move_id.operation_type == 'consume': # Subcontract partner loc _> subcontracting loc
                subcontracting_loc = self.getSubcontractingLocation()
                picking_vals = self.getPickingVals(partner_id, mrp_production_id, 'subcontracting_out')
                stock_move_vals = self.getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, customerProductionLocation, subcontracting_loc)
                new_stock_move_id = new_stock_move_id.create(stock_move_vals)
            if cancel_source_moves:
                mrp_production_id.move_raw_ids._action_cancel()
        return out_stock_picking_id

    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)

    
    def create_vendors(self):
        external_production_partner = self.env['external.production.partner']
        for seller in self.consume_bom_id.external_product.seller_ids:
            vals = {'partner_id': seller.name.id,
                    'price': seller.price,
                    'delay': seller.delay,
                    'min_qty': seller.min_qty,
                    'wizard_id': self.id}
            external_production_partner.create(vals)
        self.changeExternalPartner()


class externalWorkorderPartner(models.TransientModel):
    _name = 'external.workorder.partner'
    _description = 'Sub-Contractiong External Workorder Partner'
    
    partner_id = fields.Many2one('res.partner',
                                 string=_('External Partner'),
                                 required=True)
    default = fields.Boolean(_('Default'))
    price = fields.Float('Price',
                         default=0.0,
                         digits='Product Price',
                         required=True,
                         help="The price to purchase a product")
    delay = fields.Integer('Delivery Lead Time',
                           default=1,
                           required=True,
                           help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
    min_qty = fields.Float('Minimal Quantity',
                           default=0.0,
                           required=True,
                           help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")

    wizard_id = fields.Many2one('mrp.workorder.externally.wizard',
                                string="Vendors")


class MrpWorkorderWizard(MrpProductionWizard):
    _name = "mrp.workorder.externally.wizard"
    _inherit = ['mrp.production.externally.wizard']
    _description='Sub-Contracting Mrp Production Externally wizard'
    
    external_partner = fields.One2many('external.workorder.partner',
                                       inverse_name='wizard_id',
                                       string=_('External Partner'))

    move_raw_ids = fields.One2many('stock.tmp_move',
                                   string='Raw Materials',
                                   inverse_name='external_prod_workorder_raw',
                                   domain=[('scrapped', '=', False)])

    move_finished_ids = fields.One2many('stock.tmp_move',
                                        string='Finished Products',
                                        inverse_name='external_prod_workorder_finish',
                                        domain=[('scrapped', '=', False)])

    def getPickingVals(self, partner_id, mrp_production_id, operation_type):
        ret = super(MrpWorkorderWizard, self).getPickingVals(partner_id, mrp_production_id, operation_type)
        ret['sub_workorder_id'] = self.getWo().id
        return ret

    def getOrigin(self, productionBrws):
        mrp_workorder_id = self.getWo()
        return "%s - %s - %s" % (productionBrws.name, mrp_workorder_id.name, mrp_workorder_id.external_partner.name)

    def getStockMoveVals(self, stock_move_id, mrp_production_id, out_stock_picking_id, location_id, location_dest_id):
        ret = super(MrpWorkorderWizard, self).getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, location_id, location_dest_id)
        ret['mrp_workorder_id'] = self.getWo().id
        ret['workorder_id'] = self.getWo().id
        return ret

    def getPurchaseVals(self, external_partner):
        ret = super(MrpWorkorderWizard, self).getPurchaseVals(external_partner)
        ret['workorder_external_id'] = self.getWo().id
        return ret

    def getPurchaseLineVals(self, product, purchase, move_line):
        ret = super(MrpWorkorderWizard, self).getPurchaseLineVals(product, purchase, move_line)
        ret['workorder_external_id'] = self.getWo().id
        return ret

    def getDefaultProductionServiceProduct(self):
        mrp_workorder_id = self.getWo()
        if mrp_workorder_id.external_product:
            return mrp_workorder_id.external_product
        product_vals = self.getNewExternalProductInfo()
        newProduct = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
        if not newProduct:
            newProduct = self.env['product.product'].create(product_vals)
            newProduct.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                    message_type='notification')
            newProduct.type = 'service'
        mrp_workorder_id.external_product = newProduct
        mrp_workorder_id.operation_id.external_product = newProduct
        return newProduct
    
    @api.model
    def getNewExternalProductInfo(self):
        ret = super(MrpWorkorderWizard, self).getNewExternalProductInfo()
        workorder_id = self.getWo()
        ret['default_code'] = ret['default_code'] + "-" + workorder_id.name
        ret['name'] = ret['name'] + "-" + workorder_id.name
        return ret

    def getWo(self):
        out = self.env['mrp.workorder']
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        if model == 'mrp.workorder':
            out = relObj.browse(objIds)
        return out
        
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No partner selected"))
        pickingBrwsList = []
        mrp_workorder_id = self.getWo()
        mrp_workorder_id.write({'external_partner': self.external_partner.partner_id.id,
                                'state': 'external'})
        mrp_production_id = mrp_workorder_id.production_id
        for external_partner in self.external_partner:
            pickOut = self.createStockPickingOut(external_partner.partner_id, mrp_production_id, False)
            pickIn = self.createStockPickingIn(external_partner.partner_id, mrp_production_id, False)
            pickingBrwsList.extend((pickIn.id, pickOut.id))
            date_planned_finished = pickIn.scheduled_date
            date_planned_start = pickOut.scheduled_date
            _po_created = self.createPurchase(external_partner, pickIn)
        mrp_workorder_id.state = 'pending'
        mrp_workorder_id.date_planned_finished = date_planned_finished
        mrp_workorder_id.date_planned_start = date_planned_start
        mrp_production_id.external_pickings = [(6, 0, pickingBrwsList)]
        mrp_workorder_id.state = 'external'


    def create_vendors_from(self, partner_id):
        external_production_partner = self.env['external.workorder.partner']
        vals = {'partner_id': partner_id.id,
                'price': 0.0,
                'delay': 0.0,
                'min_qty': 0.0,
                'wizard_id': self.id
                }
        ret = external_production_partner.create(vals)
        self.changeExternalPartner('external.workorder.partner')
        return ret



