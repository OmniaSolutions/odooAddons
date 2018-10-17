'''
Created on 16 Jan 2018

@author: mboscolo
'''
from odoo.addons import decimal_precision as dp
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
import logging
import datetime
from dateutil.relativedelta import relativedelta


class TmpStockMove(models.TransientModel):
    _name = "stock.tmp_move"

    unit_factor = fields.Float('Unit Factor')
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
    external_prod_raw = fields.Many2one(comodel_name="mrp.externally.wizard",
                                        string="Raw",
                                        readonly=True)
    external_prod_finish = fields.Many2one(comodel_name="mrp.externally.wizard",
                                           string="Finished",
                                           readonly=True)
    scrapped = fields.Boolean('Scrapped', related='location_dest_id.scrap_location', readonly=True, store=True)
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]}, default=lambda self: self.env['product.uom'].search([], limit=1, order='id'))
    date_expected = fields.Datetime('Scheduled date')
    workorder_id = fields.Many2one(comodel_name='mrp.workorder', string='Workorder Id', readonly=True)

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
            wizardObj = self.env["mrp.externally.wizard"].browse(wizardId)
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
    wizard_id = fields.Many2one('mrp.externally.wizard',
                                string="Vendors")


class MrpProductionWizard(models.TransientModel):

    _name = "mrp.externally.wizard"

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
    production_id = fields.Many2one('mrp.production',
                                    string=_('Production'),
                                    readonly=True)
    request_date = fields.Datetime(string=_("Request date for the product"),
                                   default=lambda self: fields.datetime.now())
    create_purchese_order = fields.Boolean(_('Automatic create Purchase'), default=True)
    merge_purchese_order = fields.Boolean(_('Merge Purchase'), default=False)
    confirm_purchese_order = fields.Boolean(_('Confirm Purchase'), default=True)
    work_order_id = fields.Many2one('mrp.workorder',
                                    string=_('Workorder'),
                                    readonly=True)
    same_product_in_out = fields.Boolean(_('Same Product In and Out'), default=False)

    @api.onchange('request_date')
    def _request_date(self):
        for move in self.move_raw_ids:
            product_delay = move.product_id.produce_delay
            move.date_expected = fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
        for move in self.move_finished_ids:
            move.date_expected = self.request_date

    @api.multi
    def getWizardBrws(self):
        return self.browse(self._context.get('wizard_id', False))

    @api.multi
    def getParentObjectBrowse(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def cancelProductionRows(self, prodObj, workorder_brws=False):
        for lineBrws in prodObj.move_finished_ids:
            lineBrws.mrp_original_move = lineBrws.state
            lineBrws.action_cancel()
        for lineBrws in prodObj.move_raw_ids:
            # Cancel raw lines in production linked to this workorder
            if workorder_brws:
                if lineBrws.workorder_id.id != workorder_brws.id:
                    continue
            lineBrws.mrp_original_move = lineBrws.state
            lineBrws.action_cancel()

    def updateMoveLines(self, productionBrws, workOrderBrw=False):
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
                    'partner_id': external_partner.partner_id.id,
                    'note': lineBrws.note,
                    'state': 'confirmed',
                    'origin': lineBrws.origin,
                    'warehouse_id': lineBrws.warehouse_id.id,
                    'production_id': productionBrws.id,
                    'product_uom': lineBrws.product_uom.id,
                    'date_expected': datetime.datetime.now(),
                    'mrp_production_id': productionBrws.id,
                    'unit_factor': lineBrws.unit_factor
                }
                move_finished_ids.append((0, False, vals))
        product_delay = 0.0
        for lineBrws in self.move_raw_ids:
            if workOrderBrw and (workOrderBrw.id != lineBrws.workorder_id.id):
                # Skip raw generation if not linked to this workorder
                continue
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
                    'partner_id': external_partner.partner_id.id,
                    'note': lineBrws.note,
                    'state': 'confirmed',
                    'origin': lineBrws.origin,
                    'warehouse_id': lineBrws.warehouse_id.id,
                    'production_id': False,
                    'product_uom': lineBrws.product_uom.id,
                    'date_expected': fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0),
                    'mrp_production_id': productionBrws.id,
                    'unit_factor': lineBrws.unit_factor
                }
                move_raw_ids.append((0, False, vals))
        productionVals = {'move_raw_ids': move_raw_ids,
                              'move_finished_ids': move_finished_ids,
                              'state': 'external'}
        if workOrderBrw:
            del productionVals['state']
        productionBrws.write(productionVals)
        productsToCheck = list(set(productsToCheck))
        for product in self.env['product.product'].browse(productsToCheck):
            productionBrws.checkCreateReorderRule(product, productionBrws.location_src_id.get_warehouse())

    @api.multi
    def produce_production(self):
        productionBrws = self.getParentObjectBrowse()
        self.cancelProductionRows(productionBrws)
        self.updateMoveLines(productionBrws)
        date_planned_finished_wo = False
        date_planned_start_wo = False
        pickingBrwsList = []
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            pickOut = self.createStockPickingOut(partner_id, productionBrws, productionBrws)
            pickIn = self.createStockPickingIn(partner_id, productionBrws, productionBrws, pick_out=pickOut)
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pickOut.max_date
            pickingBrwsList.extend((pickIn.id, pickOut.id))
        self.createPurches()
        productionBrws.date_planned_finished_wo = date_planned_finished_wo
        productionBrws.date_planned_start_wo = date_planned_start_wo
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        movesToCancel = productionBrws.move_raw_ids.filtered(lambda m:m.mrp_original_move == False)
        movesToCancel2 = productionBrws.move_finished_ids.filtered(lambda m:m.mrp_original_move == False)
        movesToCancel += movesToCancel2
        movesToCancel.do_unreserve()
        movesToCancel.action_cancel()

    @api.multi
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No external partner set. Please provide one !!"))
        if not self.create_purchese_order and len(self.external_partner.ids) != 1:
            raise UserError(_("If you don't want to create purchase order you have to select only one partner."))
        if self.work_order_id:
            self.produce_workorder()
        else:
            self.produce_production()

    @api.multi
    def produce_workorder(self):
        workorderBrw = self.getParentObjectBrowse()
        productionBrws = workorderBrw.production_id
        self.cancelProductionRows(productionBrws, workorderBrw)
        self.updateMoveLines(productionBrws, workorderBrw)
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            pickOut = self.createStockPickingOut(partner_id, productionBrws, workorderBrw)  # mettere a posto questa che non metta i pick della roba che non fa parte dell'external production
            pickIn = self.createStockPickingIn(partner_id, productionBrws, workorderBrw, pick_out=pickOut)
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pickOut.max_date
        workorderBrw.date_planned_finished = date_planned_finished_wo
        workorderBrw.date_planned_start = date_planned_start_wo
        pickingBrwsList = [pickIn.id, pickOut.id]
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        self.createPurches(workorderBrw)  # mettere a posto questa
        workorderBrw.state = 'external'

    @api.model
    def getNewExternalProductInfo(self):
        val = {'default_code': "S-" + self.production_id.product_id.default_code or self.production_id.product_id.name,
               'type': 'service',
               'purchase_ok': True,
               'name': "[%s] %s" % (self.production_id.product_id.default_code, self.production_id.product_id.name)}
        return val

    @api.model
    def getDefaultExternalServiceProduct(self):
        """
        get the default external product suitable for the purchase
        """
        product_product_obj = self.env['product.product']
        product_brw = self.production_id.bom_id.external_product
        if product_brw:
            return product_brw
        product_vals = self.getNewExternalProductInfo()
        newProduct = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
        if not newProduct:
            newProduct = self.env['product.product'].create(product_vals)
            newProduct.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                    message_type='notification')
        self.production_id.bom_id.external_product = newProduct
        return newProduct

    @api.model
    def getPurcheseName(self, product_product):
        """
        this method could be overloaded as per customer needs
        """
        if product_product.default_code:
            return product_product.default_code + " - " + product_product.name
        else:
            return product_product.name

    @api.model
    def createSeller(self, external_production_partner, product_id, workorderBrws=False):
        for seller in product_id.seller_ids:
            if seller.name.id == external_production_partner.partner_id.id:
                return
        supplierinfo = {'name': external_production_partner.partner_id.id,
                        'sequence': max(product_id.seller_ids.mapped('sequence')) + 1 if product_id.seller_ids else 1,
                        'product_uom': product_id.uom_po_id.id,
                        'min_qty': external_production_partner.min_qty,
                        'price': external_production_partner.price,
                        'delay': external_production_partner.delay}
        if workorderBrws:
            supplierinfo['routing_id'] = workorderBrws.production_id.routing_id.id
            supplierinfo['operation_id'] = workorderBrws.operation_id.id
        vals = {'seller_ids': [(0, 0, supplierinfo)]}
        product_id.write(vals)

    @api.multi
    def createPurches(self, workorderBrws=False):
        if not self.create_purchese_order:
            return
        purchaseOrderObj = self.env['purchase.order']
        obj_product_product = self.getDefaultExternalServiceProduct()
        for toCreatePurchese in self.external_partner:
            self.createSeller(toCreatePurchese, obj_product_product, workorderBrws)
            purchaseBrws = None
            if self.merge_purchese_order:
                purchaseBrws = purchaseOrderObj.search([('partner_id', '=', toCreatePurchese.partner_id.id),
                                                        ('state', 'in', ['draft', 'sent'])
                                                        ], limit=1)
            else:
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
                          'production_external_id': self.production_id.id,
                          'sub_move_line': lineBrws.id}
                new_purchase_order_line = self.env['purchase.order.line'].create(values)
                new_purchase_order_line.onchange_product_id()
                new_purchase_order_line.date_planned = self.request_date
                new_purchase_order_line.product_qty = lineBrws.product_uom_qty
                lineBrws.purchase_order_line_subcontracting_id = new_purchase_order_line.id
            if self.confirm_purchese_order and purchaseBrws:
                purchaseBrws.button_confirm()

    @api.multi
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()

    def getOrigin(self, productionBrws, originBrw=None):
        return productionBrws.name

    def createStockPickingIn(self, partnerBrws, productionBrws, originBrw=None, pick_out=None):

        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'incoming'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        stockObj = self.env['stock.picking']
        customerProductionLocation = partnerBrws.location_id
        localStockLocation = productionBrws.location_src_id  # Taken from manufacturing order
        incomingMoves = self.getIncomingTmpMoves(productionBrws, customerProductionLocation, partnerBrws)
        toCreate = {'partner_id': partnerBrws.id,
                    'location_id': customerProductionLocation.id,
                    'location_dest_id': localStockLocation.id,
                    'min_date': productionBrws.date_planned_start,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'close',
                    'sub_production_id': self.production_id.id,
                    'pick_out': pick_out.id}
        if originBrw and originBrw._table == 'mrp_workorder': # Link picking with this workorder
            toCreate['sub_workorder_id'] = originBrw.id
        obj = stockObj.create(toCreate)
        newStockLines = []
        for outMove in incomingMoves:
            stockMove = outMove.copy(default={
                'name': outMove.product_id.display_name,
                'location_id': customerProductionLocation.id,
                'location_dest_id': localStockLocation.id,
                #'sale_line_id': outMove.sale_line_id,
                'production_id': False,
                'raw_material_production_id': False,
                'picking_id': obj.id})
            newStockLines.append(stockMove.id)
            outMove.action_cancel()
        obj.write({'move_lines': [(6, False, newStockLines)]})
        return obj

    def getIncomingTmpMoves(self, productionBrws, customerProductionLocation, partnerBrws):
        incomingMoves = []
        for productionLineBrws in productionBrws.move_finished_ids:
            if not customerProductionLocation:
                customerProductionLocation = productionLineBrws.location_id
            if productionLineBrws.state == 'confirmed' and productionLineBrws.partner_id == partnerBrws:
                incomingMoves.append(productionLineBrws)
        return incomingMoves
        
    def createStockPickingOut(self, partnerBrws, productionBrws, originBrw=None):
        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'outgoing'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        customerProductionLocation = partnerBrws.location_id
        localStockLocation = productionBrws.location_src_id  # Taken from manufacturing order
        stockObj = self.env['stock.picking']
        outGoingMoves = []
        for productionLineBrws in productionBrws.move_raw_ids:
            if not customerProductionLocation:
                customerProductionLocation = productionLineBrws.location_dest_id
            if productionLineBrws.state == 'confirmed' and productionLineBrws.partner_id == partnerBrws:
                outGoingMoves.append(productionLineBrws)
        toCreate = {'partner_id': partnerBrws.id,
                    'location_id': localStockLocation.id,
                    'location_dest_id': customerProductionLocation.id,
                    'min_date': datetime.datetime.now(),
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'open',
                    'sub_production_id': self.production_id.id}
        obj = stockObj.create(toCreate)
        newStockLines = []
        if self.same_product_in_out and originBrw._table == 'mrp_workorder':
            for incomingTmpMove in self.getIncomingTmpMoves(productionBrws, customerProductionLocation, partnerBrws):
                stockMove = incomingTmpMove.copy(default={
                                                  'name': incomingTmpMove.product_id.display_name,
                                                  'production_id': False,
                                                  'raw_material_production_id': False,
                                                  'unit_factor': incomingTmpMove.unit_factor})
                newStockLines.append(stockMove.id)
        else:
            for outMove in outGoingMoves:
                stockMove = outMove.copy(default={
                                                  'name': outMove.product_id.display_name,
                                                  'production_id': False,
                                                  'raw_material_production_id': False,
                                                  'unit_factor': outMove.unit_factor})
                stockMove.location_id = localStockLocation.id
                stockMove.location_dest_id = customerProductionLocation.id
                #stockMove.sale_line_id = outMove.sale_line_id
                newStockLines.append(stockMove.id)
                outMove.action_cancel()
        obj.write({'move_lines': [(6, False, newStockLines)]})
        return obj

    @api.multi
    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)

    @api.multi
    def create_vendors(self, production_id, workorder_id=False):
        sellers = production_id.bom_id.external_product.seller_ids
        external_production_partner = self.env['external.production.partner']
        for seller in sellers:
            if workorder_id:
                if not (workorder_id.operation_id.id == seller.operation_id.id):
                    continue
            vals = {'partner_id': seller.name.id,
                    'price': seller.price,
                    'delay': seller.delay,
                    'min_qty': seller.min_qty,
                    'wizard_id': self.id,
                    'operation_id': seller.operation_id.id}
            external_production_partner.create(vals)
