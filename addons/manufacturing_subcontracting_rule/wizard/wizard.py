'''
Created on 16 Jan 2018

@author: mboscolo
'''
from odoo.addons import decimal_precision as dp
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime
from dateutil.relativedelta import relativedelta


class TmpStockMove(models.TransientModel):
    _name = "stock.tmp_move"
    _table = "stock_tmp_move"

    name = fields.Char('Description', index=True, required=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('stock.move'),
        index=True, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], index=True, required=True,
        states={'done': [('readonly', True)]})
    product_uom_qty = fields.Float('Quantity',
                                   digits=dp.get_precision('Product Unit of Measure'),
                                   default=1.0, required=True, states={'done': [('readonly', True)]},
                                   help="This is the quantity of products from an inventory "
                                        "point of view. For moves in the state 'done', this is the "
                                        "quantity of products that were actually moved. For other "
                                        "moves, this is the quantity of product that is planned to "
                                        "be moved. Lowering this quantity does not generate a "
                                        "backorder. Changing this quantity on assigned moves affects "
                                        "the product reservation, and should be done with care.")
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
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
    # production filed
    external_prod_raw = fields.Many2one(comodel_name="mrp.production.externally.wizard",
                                        string="Raw",
                                        readonly=True)
    external_prod_finish = fields.Many2one(comodel_name="mrp.production.externally.wizard",
                                           string="Finished",
                                           readonly=True)
    # workorder field
    external_prod_workorder_raw = fields.Many2one(comodel_name="mrp.workorder.externally.wizard",
                                                  string="Raw",
                                                  readonly=True)
    external_prod_workorder_finish = fields.Many2one(comodel_name="mrp.workorder.externally.wizard",
                                                     string="Finished",
                                                     readonly=True)
    scrapped = fields.Boolean('Scrapped', related='location_dest_id.scrap_location', readonly=True, store=True)
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]}, default=lambda self: self.env['product.uom'].search([], limit=1, order='id'))
    date_expected = fields.Datetime('Scheduled date')

    @api.model
    def default_get(self, fields_list):
        context = self.env.context
        res = super(TmpStockMove, self).default_get(fields_list)
        wh = context.get('warehouse_id', False)
        if wh:
            res['warehouse_id'] = wh
            res['name'] = self.env['stock.warehouse'].browse(res['warehouse_id']).display_name
        wizardId = context.get('wizard_obj_id', False)
        if wizardId:
            wizardObj = self.env["mrp.production.externally.wizard"].browse(wizardId)
            res['location_id'] = wizardObj.production_id.location_src_id.id
        return res

    @api.model
    def create(self, vals):
        return super(TmpStockMove, self).create(vals)


class externalProductionPartner(models.TransientModel):
    _name = 'external.production.partner'
    partner_id = fields.Many2one('res.partner',
                                 string=_('External Partner'),
                                 required=True)
    default = fields.Boolean(_('Default'))
    price = fields.Float('Price',
                         default=0.0,
                         digits=dp.get_precision('Product Price'),
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
    consume_product_id = fields.Many2one(comodel_name='product.product',
                                         string=_('Product To Consume'))
    consume_bom_id = fields.Many2one(comodel_name='mrp.bom',
                                     string=_('BOM To Consume'))
    external_warehouse_id = fields.Many2one('stock.warehouse',
                                            string=_('External Warehouse'))
    external_location_id = fields.Many2one('stock.location',
                                           string=_('External Location'))
    production_id = fields.Many2one('mrp.production',
                                    string=_('Production'),
                                    readonly=True)
    request_date = fields.Datetime(string=_("Request date for the product"),
                                   default=lambda self: fields.datetime.now())
    create_purchese_order = fields.Boolean(_('Automatic create Purchase'))
    merge_purchese_order = fields.Boolean(_('Merge Purchase'), default=True)

    @api.onchange('consume_product_id')
    def _consume_product_id(self):
        # check if the product have bom in case not error
        # update the bom with the first one
        # create new in move in order to get the the corrisponding out object
        pass

    @api.onchange('consume_product_id')
    def _consume_bom_id(self):
        # create the row material related to the bom chosen
        # if the @api.onchange('consume_product_id') may the @api.onchange('consume_product_id') should be fired to
        # so we can be sure that the raw material is updated for the wizar
        pass

    @api.onchange('request_date')
    def _request_date(self):
        for move in self.move_raw_ids:
            product_delay = move.product_id.produce_delay
            move.date_expected = fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
        for move in self.move_finished_ids:
            move.date_expected = self.request_date

    @api.onchange('external_location_id')
    def _external_location_id(self):
        for line in self.move_finished_ids:
            line.location_id = self.external_location_id.id
        for line in self.move_raw_ids:
            line.location_dest_id = self.external_location_id.id

    @api.onchange('consume_bom_id')
    def changeBOMId(self):
        self.operationTypeChanged()

    @api.multi
    def getWizardBrws(self):
        return self.browse(self._context.get('wizard_id', False))

    @api.onchange('operation_type')
    def operationTypeChanged(self):
        prodObj = self.getParentProduction()
        wBrws = self.getWizardBrws()
        cleanRelInfos = {'raw_material_production_id': False,
                         'origin': ''}
        manOrderRawLines = prodObj.copyAndCleanLines(prodObj.move_raw_ids)
        manOrderFinishedLines = prodObj.copyAndCleanLines(prodObj.move_finished_ids)
        if self.operation_type == 'normal':
            wBrws.write({'move_raw_ids': [(6, 0, manOrderRawLines)],
                         'move_finished_ids': [(6, 0, manOrderFinishedLines)]
                         })
            self.move_raw_ids = [(6, 0, manOrderRawLines)]
            self.move_finished_ids = [(6, 0, manOrderFinishedLines)]
        elif self.operation_type == 'consume':
            _boms, lines = self.consume_bom_id.explode(self.consume_product_id, 1, picking_type=self.consume_bom_id.picking_type_id)
            moves = prodObj._generate_raw_moves(lines)
            moves.write(cleanRelInfos)
            wBrws.write({'move_raw_ids': [(6, 0, moves.ids)],
                         'move_finished_ids': [(6, 0, manOrderFinishedLines)]
                         })
            self.move_raw_ids = [(6, 0, moves.ids)]
            self.move_finished_ids = [(6, 0, manOrderFinishedLines)]

    @api.multi
    def getParentProduction(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def cancelProductionRows(self, prodObj):
        for lineBrws in prodObj.move_raw_ids + prodObj.move_finished_ids:
            lineBrws.mrp_original_move = lineBrws.state
            lineBrws.action_cancel()

    def updateMoveLines(self, productionBrws):
        move_raw_ids = []
        move_finished_ids = []
        productsToCheck = []
        for lineBrws in self.move_finished_ids:
            productsToCheck.append(lineBrws.product_id.id)
            for external_partner in self.external_partner:
                vals = {
                    'name': lineBrws.name,
                    'company_id': lineBrws.company_id.id,
                    'product_id': lineBrws.product_id.id,
                    'product_uom_qty': lineBrws.product_uom_qty,
                    'location_id': lineBrws.location_id.id,
                    'location_dest_id': lineBrws.location_dest_id.id,
                    'partner_id': external_partner.id,
                    'note': lineBrws.note,
                    'state': 'confirmed',
                    'origin': lineBrws.origin,
                    'warehouse_id': lineBrws.warehouse_id.id,
                    'production_id': productionBrws.id,
                    'product_uom': lineBrws.product_uom.id,
                    'date_expected': datetime.datetime.now(),
                }
                move_finished_ids.append((0, False, vals))
        product_delay = 0.0
        for lineBrws in self.move_raw_ids:
            productsToCheck.append(lineBrws.product_id.id)
            product_delay = lineBrws.product_id.produce_delay
            for external_partner in self.external_partner:
                vals = {
                    'name': lineBrws.name,
                    'company_id': lineBrws.company_id.id,
                    'product_id': lineBrws.product_id.id,
                    'product_uom_qty': lineBrws.product_uom_qty,
                    'location_id': lineBrws.location_id.id,
                    'location_dest_id': lineBrws.location_dest_id.id,
                    'partner_id': external_partner.id,
                    'note': lineBrws.note,
                    'state': 'confirmed',
                    'origin': lineBrws.origin,
                    'warehouse_id': lineBrws.warehouse_id.id,
                    'production_id': False,
                    'product_uom': lineBrws.product_uom.id,
                    'date_expected': fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
                }
                move_raw_ids.append((0, False, vals))
        productionBrws.write({'move_raw_ids': move_raw_ids,
                              'move_finished_ids': move_finished_ids,
                              'state': 'external',
                              'external_partner': (6, 0, [self.external_partner.ids])})
        productsToCheck = list(set(productsToCheck))
        for product in self.env['product.product'].browse(productsToCheck):
            productionBrws.checkCreateReorderRule(product, productionBrws.location_src_id.get_warehouse())

    @api.multi
    def button_produce_externally(self):
        productionBrws = self.getParentProduction()
        self.cancelProductionRows(productionBrws)
        self.updateMoveLines(productionBrws)
        date_planned_finished_wo = False
        date_planned_start_wo = False
        for external_partner in self.external_partner:
            pickIn = self.createStockPickingIn(external_partner, productionBrws)
            pickOut = self.createStockPickingOut(external_partner, productionBrws)
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pickOut.max_date
        productionBrws.date_planned_finished = date_planned_finished_wo
        productionBrws.date_planned_start = date_planned_start_wo
        #  productionBrws.date_planned_finished_wo = date_planned_finished_wo
        #  productionBrws.date_planned_start_wo = date_planned_start_wo
        pickingBrwsList = [pickIn.id, pickOut.id]
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        self.createPurches()

    @api.model
    def getNewExternalProductInfo(self):
        val = {'default_code': "S-" + self.production_id.product_id.default_code,
               'type': 'service',
               'purchase_ok': True,
               'name': "[%s] %s" % (self.production_id.product_id.default_code, self.production_id.product_id.name)}
        return val

    @api.model
    def getDefaultExternalServiceProduct(self):
        """
        get the default external product suitable for the purchase
        """
        bom_product = self.production_id.bom_id.external_product
        if bom_product:
            return bom_product
        product_brw = self.env['product.product'].search([('default_code', '=', 'external_service')])
        if product_brw:
            return product_brw
        return self.env['product.product'].create(self.getNewExternalProductInfo())

    @api.model
    def getPurcheseName(self, product_product):
        """
        this method could be overloaded as per customer needs
        """
        if product_product.default_code:
            return product_product.default_code + " - " + product_product.name
        else:
            return product_product.name

    @api.multi
    def createPurches(self):
        if not self.create_purchese_order:
            return
        purchaseOrderObj = self.env['purchase.order']
        obj_product_product = self.getDefaultExternalServiceProduct()
        for toCreatePurchese in self.external_partner:
            purchaseBrws = None
            if self.merge_purchese_order:
                purchaseBrws = purchaseOrderObj.search([('partner_id', '=', self.external_partner.id),
                                                        ('state', 'in', ['draft', 'sent'])
                                                        ], limit=1)
            if not purchaseBrws:
                purchaseBrws = purchaseOrderObj.create({'partner_id': toCreatePurchese.partner_id.id,
                                                        'date_planned': self.request_date,
                                                        'production_external_id': self.production_id.id})

            for lineBrws in self.move_finished_ids:
                values = {'product_id': obj_product_product.id,
                          'name': self.getPurcheseName(obj_product_product),
                          'product_qty': lineBrws.product_uom_qty,
                          'product_uom': obj_product_product.uom_po_id.id,
                          'price_unit': obj_product_product.price,
                          'date_planned': self.request_date,
                          'order_id': purchaseBrws.id,
                          'production_external_id': self.production_id.id}
                new_product_line = self.env['purchase.order.line'].create(values)
                new_product_line.onchange_product_id()

    @api.multi
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()

    def getOrigin(self, productionBrws, originBrw=None):
        return productionBrws.name

    def createStockPickingIn(self, partner, productionBrws, originBrw=None):

        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'incoming'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        stockObj = self.env['stock.picking']
        customerProductionLocation = self.external_location_id
        localStockLocation = productionBrws.location_src_id  # Taken from manufacturing order
        incomingMoves = []
        for productionLineBrws in productionBrws.move_finished_ids:
            if productionLineBrws.state == 'confirmed':
                incomingMoves.append(productionLineBrws)
        toCreate = {'partner_id': partner.id,
                    'location_id': customerProductionLocation.id,
                    'location_src_id': customerProductionLocation.id,
                    'location_dest_id': localStockLocation.id,
                    'min_date': productionBrws.date_planned_start,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'close',
                    'sub_production_id': self.production_id}
        obj = stockObj.create(toCreate)
        newStockLines = []
        for outMove in incomingMoves:
            stockMove = outMove.copy(default={'production_id': False,
                                              'raw_material_production_id': False})
            newStockLines.append(stockMove.id)
        obj.write({'move_lines': [(6, False, newStockLines)]})
        return obj

    def createStockPickingOut(self, partner, productionBrws, originBrw=None):
        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'outgoing'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        customerProductionLocation = self.external_location_id
        localStockLocation = productionBrws.location_src_id  # Taken from manufacturing order
        stockObj = self.env['stock.picking']
        outGoingMoves = []
        for productionLineBrws in productionBrws.move_raw_ids:
            if productionLineBrws.state == 'confirmed':
                outGoingMoves.append(productionLineBrws)
        toCreate = {'partner_id': partner.id,
                    'location_id': localStockLocation.id,
                    'location_dest_id': customerProductionLocation.id,
                    'location_src_id': localStockLocation.id,
                    'min_date': datetime.datetime.now(),
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'open',
                    'sub_production_id': self.production_id}
        obj = stockObj.create(toCreate)
        newStockLines = []
        for outMove in outGoingMoves:
            stockMove = outMove.copy(default={'production_id': False,
                                              'raw_material_production_id': False})
            newStockLines.append(stockMove.id)
        obj.write({'move_lines': [(6, False, newStockLines)]})
        return obj

    @api.multi
    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)
#  operation_id e' l'operazione del ruting che vado a fare mi da 'oggetto

    @api.multi
    def create_vendors(self):
        external_production_partner = self.env['external.production.partner']
        for seller in self.consume_bom_id.external_product.seller_ids:
            vals = {'partner_id': seller.name.id,
                    'price': seller.price,
                    'delay': seller.delay,
                    'min_qty': seller.min_qty,
                    'wizard_id': self.id}
            external_production_partner.create(vals)


class MrpWorkorderWizard(MrpProductionWizard):
    _name = "mrp.workorder.externally.wizard"
    _inherit = ['mrp.production.externally.wizard']

    move_raw_ids = fields.One2many('stock.tmp_move',
                                   string='Raw Materials',
                                   inverse_name='external_prod_workorder_raw',
                                   domain=[('scrapped', '=', False)])

    move_finished_ids = fields.One2many('stock.tmp_move',
                                        string='Finished Products',
                                        inverse_name='external_prod_workorder_finish',
                                        domain=[('scrapped', '=', False)])

    @api.multi
    def button_produce_externally(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        workorderBrws = relObj.browse(objIds)
        workorderBrws.write({'external_partner': self.external_partner.id,
                             'state': 'external'})
        productionBrws = workorderBrws.production_id
        pickIn = self.createStockPickingIn(self.external_partner, productionBrws, workorderBrws)
        pickOut = self.createStockPickingOut(self.external_partner, productionBrws, workorderBrws)
        productionBrws.date_planned_finished = pickIn.max_date
        productionBrws.date_planned_start = pickOut.max_date
        productionBrws.button_unreserve()   # Needed to evaluate picking out move

    def getOrigin(self, productionBrws, originBrw):
        return "%s - %s - %s" % (productionBrws.name, originBrw.name, originBrw.external_partner.name)
