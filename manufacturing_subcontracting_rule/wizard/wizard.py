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
import json
import datetime
from dateutil.relativedelta import relativedelta


class MrpProductionWizard(models.Model):

    _name = "mrp.externally.wizard"
    _table = 'mrp_externally_wizard'

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
    work_order_id = fields.Many2one('mrp.workorder',
                                    string=_('Workorder'),
                                    readonly=True)
    request_date = fields.Datetime(string=_("Request date for the product"),
                                   default=lambda self: fields.datetime.now())
    create_purchese_order = fields.Boolean(_('Automatic create Purchase'), default=True)
    merge_purchese_order = fields.Boolean(_('Merge Purchase'), default=False)
    confirm_purchese_order = fields.Boolean(_('Confirm Purchase'), default=False)
    select_external_partner_ids = fields.Char(string=_('Select Partners'),
                                              compute='_compute_select_external_partner')
    select_external_partner = fields.Many2one('res.partner',
                                    string=_('External Partner Stock'))
    external_operation = fields.Selection([('normal', 'Normal'),
                                           ('parent', 'Parent'),
                                           ('operation', 'Operation')],
                                           default='normal',
                                           string=_('Produce it externally automatically as'),
                                           help="""Normal: Use the Parent object as Product for the Out Pickings and the raw material for the Out Picking
                                                   Parent: Use the Parent product for the In Out pickings
                                                   Operation: Use the Product that have the Operation assigned for the In Out pickings""")


    ######Deprecated########
    is_by_operation = fields.Boolean(default=False,
                                     string="Is computed by operation",
                                     help="""Push out and pull in only the product that have operation""")
    is_some_product = fields.Boolean(_('Same Product In and Out'), default=False)
    ########################

    @api.multi
    @api.depends('external_partner')
    def _compute_select_external_partner(self):
        for wizardBrws in self:
            partnerIds = []
            for external_partner_brws in wizardBrws.external_partner:
                partnerIds.append(external_partner_brws.partner_id.id)
            self.select_external_partner_ids = json.dumps(partnerIds)
            if not partnerIds:
                self.select_external_partner = False

    @api.multi
    def compute_stock(self):
        for wizardObj in self:
            return wizardObj.updateStockQuant(wizardObj.select_external_partner.location_id)

    @api.multi
    def updateStockQuant(self, forceLocation=False):
        stockQuantObj = self.env['stock.quant']
        for wizardBrws in self:
            if not forceLocation:
                stockWarehouseBrws = self.env.ref('stock.warehouse0')
                forceLocation = stockWarehouseBrws.lot_stock_id
            # Raw moves
            for tmpMoveBrws in wizardBrws.move_raw_ids:
                prodBrws = tmpMoveBrws.product_id
                quantObjBrwsList = stockQuantObj.search([
                    ('location_id', '=', forceLocation.id),
                    ('product_id', '=', prodBrws.id),
                    ], limit=1)
                qty = 0
                for quantBrws in quantObjBrwsList:
                    qty = quantBrws.qty
                tmpMoveBrws.location_available = forceLocation.id
                tmpMoveBrws.qty_available = qty
            # Finished moves
            for tmpMoveBrws in wizardBrws.move_finished_ids:
                prodBrws = tmpMoveBrws.product_id
                quantObjBrwsList = stockQuantObj.search([
                    ('location_id', '=', forceLocation.id),
                    ('product_id', '=', prodBrws.id),
                    ], limit=1)
                qty = 0
                for quantBrws in quantObjBrwsList:
                    qty = quantBrws.qty
                tmpMoveBrws.location_available = forceLocation.id
                tmpMoveBrws.qty_available = qty
            
            ctx = self.env.context.copy()
            ctx['wizard_id'] = wizardBrws.id
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.externally.wizard',
                'view_mode': 'form,tree',
                'view_type': 'form',
                'res_id': wizardBrws.id,
                'context': ctx,
                'target': 'new',
            }
        
    @api.onchange('request_date')
    def _request_date(self):
        for move in self.move_raw_ids:
            product_delay = move.product_id.produce_delay
            move.date_expected = fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
        for move in self.move_finished_ids:
            move.date_expected = self.request_date

    @api.multi
    def getParentObjectBrowse(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def checkCreateReorderRule(self, productionBrws):
        productsToCheck = []
        for lineBrws in self.move_finished_ids:
            productsToCheck.append(lineBrws.product_id.id)
        for lineBrws in self.move_raw_ids:
            productsToCheck.append(lineBrws.product_id.id)
        warehouse = productionBrws.location_src_id.get_warehouse()
        for product in self.env['product.product'].browse(productsToCheck):
            productionBrws.checkCreateReorderRule(product, warehouse)

    @api.multi
    def produce_production(self):
        productionBrws = self.getParentObjectBrowse()
        self.checkCreateReorderRule(productionBrws)
        date_planned_finished_wo = False
        date_planned_start_wo = False
        pickingBrwsList = []
        productionLocation = productionBrws.product_id.property_stock_production    # Production location
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            customerProductionLocation = self.getCustomerLocation(partner_id)
            pick_out_ids = self.createStockPickingOutProductionOrder(partner_id, productionBrws, customerProductionLocation, productionLocation)
            pickIn = self.createStockPickingInProdOrder(partner_id, productionBrws, customerProductionLocation, productionLocation, pick_out_ids[0])
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pick_out_ids[0].max_date
            if pickIn:
                pickingBrwsList.append(pickIn.id)
            for pick_out in pick_out_ids:
                pickingBrwsList.append(pick_out.id)
        self.createPurches(pickIn, production=productionBrws)
        productionBrws.date_planned_finished_wo = date_planned_finished_wo
        productionBrws.date_planned_start_wo = date_planned_start_wo
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        productionBrws.state = 'external'
        self.updateMOLinesWithDifferences(productionBrws)

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
        for move_id in self.move_raw_ids:
            move_id.state = 'cancel'
        self.move_raw_ids.unlink()
        for move_id in self.move_finished_ids:
            move_id.state = 'cancel'
        self.move_finished_ids.unlink()
        self.unlink()
        return True

    def updateMOLinesWithDifferences(self, productionBrws):
        '''
            Update manufacturing order with quantities and products added / removed in the wizard
        '''
        if self.external_operation == 'normal':
            firstRawMove = False
            for prod_raw_move in productionBrws.move_raw_ids:
                firstRawMove = prod_raw_move
            for raw_move in self.move_raw_ids:
                if raw_move.operation_type == 'deliver_consume':
                    if raw_move.source_production_move:
                        if raw_move.source_production_move.product_uom_qty != raw_move.product_uom_qty:
                            raw_move.source_production_move.product_uom_qty = raw_move.product_uom_qty
                        if raw_move.source_production_move.product_id != raw_move.product_id:
                            raw_move.source_production_move.product_id = raw_move.product_id
                        if raw_move.source_production_move.unit_factor != raw_move.unit_factor:
                            raw_move.source_production_move.unit_factor = raw_move.unit_factor
                    else:
                        new_move = firstRawMove.copy(self.getTmpMoveVals(raw_move))
                        new_move.action_confirm()
            firstFinishMove = False
            for prod_finish_move in productionBrws.move_finished_ids:
                firstFinishMove = prod_finish_move
            finished_qty = 0
            for finish_move in self.move_finished_ids:
                if finish_move.source_production_move:
                    if finish_move.source_production_move.product_id != finish_move.product_id:
                        continue
                    if finish_move.source_production_move.product_uom_qty != finish_move.product_uom_qty:
                        finish_move.source_production_move.product_uom_qty = finish_move.product_uom_qty
                    if finish_move.source_production_move.unit_factor != finish_move.unit_factor:
                        if productionBrws.product_id == finish_move.product_id:
                            raise UserError(_("You can't change manufacturing finished product unit factor"))
                        finish_move.source_production_move.unit_factor = finish_move.unit_factor
                    if productionBrws.product_id == finish_move.product_id:
                        finished_qty += finish_move.product_uom_qty
                else:
                    new_move = firstFinishMove.copy(self.getTmpMoveVals(finish_move))
                    new_move.action_confirm()
                    if productionBrws.product_id == new_move.product_id:
                        finished_qty += new_move.product_uom_qty
            if finished_qty != productionBrws.product_qty:
                raise UserError(_('You cannot produce different quantity that expected in production order.\n Expected %r, producing %r') % (productionBrws.product_qty, finished_qty))

    def getTmpMoveVals(self, tmp_move):
        return {
            'product_id': tmp_move.product_id.id,
            'product_uom_qty': tmp_move.product_uom_qty,
            'product_uom': tmp_move.product_uom.id,
            'name': tmp_move.name,
            'origin': tmp_move.origin,
            'date_expected': tmp_move.date_expected,
            'unit_factor': tmp_move.unit_factor,
                    }

    @api.multi
    def setupOptions(self, workorderBrw):
        if workorderBrw.operation_id.external_operation in ['normal', '', False]:
            self.external_operation = 'normal'
        # check parent input - output
        raw = {'product_to_produce': 0}
        finished = {'product_to_produce': 0}
        product_to_produce = workorderBrw.production_id.product_id
        for line in self.move_raw_ids:
            if line.product_id == product_to_produce:
                raw['product_to_produce'] += line.product_uom_qty
        if raw['product_to_produce'] > 0:
            for line in self.move_finished_ids:
                if line.product_id == product_to_produce:
                    finished['product_to_produce'] += line.product_uom_qty
        if raw['product_to_produce'] == finished['product_to_produce'] and raw['product_to_produce'] > 0:
            self.external_operation = 'parent'

    @api.multi
    def produce_workorder(self):
        workorderBrw = self.getParentObjectBrowse()
        productionBrws = workorderBrw.production_id
        self.checkCreateReorderRule(productionBrws)
        self.setupOptions(workorderBrw)
        pickingBrwsList = []
        productionLocation = productionBrws.product_id.property_stock_production
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            customerProductionLocation = self.getCustomerLocation(partner_id)
            picksOut = self.createStockPickingOutWorkorder(partner_id, productionBrws, customerProductionLocation, productionLocation, workorderBrw)
            pickIn = self.createStockPickingInWorkOrder(partner_id, productionBrws, customerProductionLocation, productionLocation, workorderBrw, picksOut[0])
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = picksOut[0].max_date
            if pickIn:
                pickingBrwsList.append(pickIn.id)
            for pickOut in picksOut:
                pickingBrwsList.append(pickOut.id)
        workorderBrw.date_planned_finished = date_planned_finished_wo
        workorderBrw.date_planned_start = date_planned_start_wo
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        self.createPurches(pickIn, workorderBrw)
        workorderBrw.state = 'external'
        self.updateMOLinesWithDifferences(productionBrws)
        if not pickIn:
            workorderBrw.closeWO()

    @api.model
    def getNewExternalProductInfo(self):
        if not self.production_id.product_id.default_code:
            raise UserError("No default code Assigned to product %r " % self.production_id.product_id.name)
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
    def createPurches(self, pickIn, workorderBrws=False, production=False):
        if not self:
            return
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
            if not purchaseBrws and self.create_purchese_order:
                vals = {'partner_id': toCreatePurchese.partner_id.id,
                        'date_planned': self.request_date}
                if production:
                    vals['production_external_id'] = production.id
                if workorderBrws:
                    vals['workorder_external_id'] = workorderBrws.id
                purchaseBrws = purchaseOrderObj.create(vals)

            for lineBrws in pickIn.move_lines:
                values = {'product_id': obj_product_product.id,
                          'name': self.getPurcheseName(obj_product_product),
                          'product_qty': lineBrws.product_uom_qty,
                          'product_uom': obj_product_product.uom_po_id.id,
                          'price_unit': obj_product_product.price,
                          'date_planned': self.request_date,
                          'order_id': purchaseBrws.id,
                          'sub_move_line': lineBrws.id}
                if production:
                    values['production_external_id'] = production.id
                if workorderBrws:
                    values['workorder_external_id'] = workorderBrws.id
                new_purchase_order_line = self.env['purchase.order.line'].create(values)
                new_purchase_order_line.onchange_product_id()
                new_purchase_order_line.date_planned = self.request_date
                new_purchase_order_line.product_qty = lineBrws.product_uom_qty
                lineBrws.purchase_order_line_subcontracting_id = new_purchase_order_line.id
                lineBrws.purchase_line_id = new_purchase_order_line.id
            if self.confirm_purchese_order and purchaseBrws:
                purchaseBrws.button_confirm()

    @api.multi
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()

    def getOriginProdOrder(self, productionBrws):
        return productionBrws.name

    def getOriginWorkOrder(self, productionBrws, workorderBrw, partner_id):
        return "%s - %s - %s" % (productionBrws.name, workorderBrw.name, partner_id.name)

    def createStockPickingInProdOrder(self, partner_id, productionBrws, customerProductionLocation, productionLocation, pick_out=None):
        stock_piking = self.env['stock.picking']
        if not self.move_finished_ids:
            return stock_piking
        origin = self.getOriginProdOrder(productionBrws)
        toCreate = self.getStockPickingInVals(partner_id, customerProductionLocation, productionLocation, productionBrws, pick_out, origin)
        obj = stock_piking.create(toCreate)
        for stock_move_id in self.move_finished_ids:
            vals = stock_move_id.read()[0]
            self.cleanReadVals(vals)
            stockMove = self.env['stock.move'].create(vals)
            stockMove.name = stock_move_id.product_id.display_name
            stockMove.location_id = customerProductionLocation.id
            stockMove.location_dest_id = productionLocation.id
            stockMove.production_id = False
            stockMove.unit_factor = stock_move_id.unit_factor
            stockMove.mrp_workorder_id = self.work_order_id.id
            stockMove.raw_material_production_id = False
            stockMove.picking_id = obj.id
            stockMove.state = 'draft'
        return obj

    def getStockPickingInVals(self, partner_id, customerProductionLocation, productionLocation, productionBrws, pick_out, origin, sub_workorder_id=False):
        return {'partner_id': partner_id.id,
                'location_id': customerProductionLocation.id,
                'location_dest_id': productionLocation.id,
                'min_date': productionBrws.date_planned_start,
                'move_type': 'direct',
                'picking_type_id': self.getPickingType(productionBrws, 'incoming'),
                'origin': origin,
                'move_lines': [],
                'state': 'draft',
                'sub_contracting_operation': 'close',
                'sub_production_id': productionBrws.id,
                'pick_out': pick_out.id,
                'sub_workorder_id': sub_workorder_id,
                }

    def createStockPickingInWorkOrder(self, partner_id, productionBrws, customerProductionLocation, productionLocation, workorderBrw, pick_out=None):
        stock_piking = self.env['stock.picking']
        move_obj = self.env['stock.move']
        if not self.move_finished_ids:
            return stock_piking
        origin = self.getOriginWorkOrder(productionBrws, workorderBrw, partner_id)
        toCreate = self.getStockPickingInVals(partner_id, customerProductionLocation, productionLocation, productionBrws, pick_out, origin, workorderBrw.id)
        picking = stock_piking.create(toCreate)
        if self.external_operation == 'operation':     # Operation in-out
            moveToClone = None
            for stock_move_id in self.move_finished_ids:
                moveToClone = stock_move_id
                break
            for bom_line in productionBrws.bom_id.bom_line_ids:
                if bom_line.operation_id == workorderBrw.operation_id:
                    vals = moveToClone.read()[0]
                    self.cleanReadVals(vals)
                    newMove = move_obj.create(vals)
                    newMove.product_id = bom_line.product_id.id
                    newMove.product_uom_qty = bom_line.product_qty
                    self.updatePickInMove(newMove, productionLocation, customerProductionLocation, workorderBrw, picking)
        else:
            if self.external_operation in ['normal', 'parent']:
                for tmpRow in self.move_finished_ids:
                    vals = tmpRow.read()[0]
                    self.cleanReadVals(vals)
                    newMove = move_obj.create(vals)
                    newMove.unit_factor = tmpRow.unit_factor
                    self.updatePickInMove(newMove, productionLocation, customerProductionLocation, workorderBrw, picking)
                    self.updateMOProducedFlag(workorderBrw, tmpRow.product_id)
        return picking

    def updateMOProducedFlag(self, workorderBrw, product):
        if not workorderBrw.is_mo_produced:
            if self.production_id.product_id == product:
                for wo in self.production_id.workorder_ids:
                    wo.is_mo_produced = True
        elif self.production_id.product_id == product:
            raise UserError('You cannot produce more than one time finished products of the manufacturing order.')

    def updatePickInMove(self, newMove, productionLocation, customerProductionLocation, workorderBrw, picking):
        newMove.location_id = customerProductionLocation.id
        newMove.location_dest_id = productionLocation.id
        newMove.state = 'draft'
        newMove.production_id = False
        newMove.mrp_original_move = False
        newMove.raw_material_production_id = False
        newMove.picking_id = picking.id
        newMove.workorder_id = workorderBrw.id
        newMove.mrp_workorder_id = workorderBrw.id

    def getCustomerLocation(self, partner_id):
        customerProductionLocation = partner_id.location_id
        if not customerProductionLocation:
            raise UserError(_('Partner %s has not location setup.' % (partner_id.name)))
        return customerProductionLocation

    def getPickingType(self, productionBrws, pick_type='outgoing'):
        warehouseId = productionBrws.picking_type_id.warehouse_id.id
        pickTypeObj = self.env['stock.picking.type']
        for pick in pickTypeObj.search([('code', '=', pick_type),
                                        ('active', '=', True),
                                        ('warehouse_id', '=', warehouseId)]):
            return pick.id
        return False

    def createStockPickingOutProductionOrder(self, partner_id, productionBrws, customerProductionLocation, productionLocation):
        pick_out_ids = []
        stock_piking = self.env['stock.picking']
        if not self.move_raw_ids:
            return [stock_piking]
        origin = self.getOriginProdOrder(productionBrws)
        toCreate = self.getStockPickingOutVals(partner_id, productionLocation, customerProductionLocation, productionBrws, origin)
        pick_out = stock_piking.create(toCreate)
        pick_out_ids.append(pick_out)
        only_deliver_moves = []
        for stock_move_id in self.move_raw_ids:
            if stock_move_id.operation_type == 'deliver_consume':
                # Manufacturing - Subcontracting moves
                vals = stock_move_id.read()[0]
                self.cleanReadVals(vals)
                stockMove = self.env['stock.move'].create(vals)
                stockMove.name = stock_move_id.product_id.display_name
                stockMove.unit_factor = stock_move_id.unit_factor
                stockMove.location_id = productionLocation.id
                stockMove.location_dest_id = customerProductionLocation.id
                stockMove.picking_id = pick_out.id
                stockMove.state = 'draft'
            elif stock_move_id.operation_type == 'deliver':
                only_deliver_moves.append(stock_move_id)
        if only_deliver_moves:
            # Create picking to consume material delivered stock --> customer
            warehouse_production = productionBrws.location_dest_id.get_warehouse()
            stock_location = warehouse_production.lot_stock_id
            toCreate = self.getStockPickingOutVals(partner_id, stock_location, customerProductionLocation, productionBrws, origin)
            pick_out_2 = stock_piking.create(toCreate)
            for move in only_deliver_moves:
                vals = move.read()[0]
                self.cleanReadVals(vals)
                stockMove = self.env['stock.move'].create(vals)
                stockMove.name = move.product_id.display_name
                stockMove.unit_factor = move.unit_factor
                stockMove.location_id = stock_location.id
                stockMove.location_dest_id = customerProductionLocation.id
                stockMove.picking_id = pick_out_2.id
                stockMove.state = 'draft'
            pick_out_ids.append(pick_out_2)
        return pick_out_ids

    def cleanReadVals(self, vals):
        self.env['mrp.production'].cleanReadVals(vals)

    def createStockPickingOutWorkorder(self, partner_id, productionBrws, customerProductionLocation, productionLocation, workorderBrw):
        stock_piking = self.env['stock.picking']
        move_obj = self.env['stock.move']
        if not self.move_raw_ids:
            return [stock_piking]
        out_picks = []
        origin = self.getOriginWorkOrder(productionBrws, workorderBrw, partner_id)
        toCreate = self.getStockPickingOutVals(partner_id, productionLocation, customerProductionLocation, productionBrws, origin, sub_workorder_id=workorderBrw.id)
        picking = stock_piking.create(toCreate)
        out_picks.append(picking)
        if self.external_operation == 'parent':   # Parent in - out
            for stock_move_id in self.move_finished_ids:
                vals = stock_move_id.read()[0]
                self.cleanReadVals(vals)
                newMove = move_obj.create(vals)
                newMove.unit_factor = stock_move_id.unit_factor
                self.updatePickOutMove(newMove, productionLocation, customerProductionLocation, workorderBrw, picking)
        elif self.external_operation == 'operation':     # Operation in-out
            moveToClone = None
            for stock_move_id in self.move_finished_ids:
                moveToClone = stock_move_id
                break
            for bom_line in productionBrws.bom_id.bom_line_ids:
                if bom_line.operation_id == workorderBrw.operation_id:
                    vals = moveToClone.read()[0]
                    self.cleanReadVals(vals)
                    newMove = move_obj.create(vals)
                    newMove.product_id = bom_line.product_id.id
                    newMove.product_uom_qty = bom_line.product_qty
                    self.updatePickOutMove(newMove, productionLocation, customerProductionLocation, workorderBrw, picking)
        else:
            only_deliver_moves = []
            for stock_move_id in self.move_raw_ids:
                if stock_move_id.operation_type == 'deliver_consume':
                    vals = stock_move_id.read()[0]
                    self.cleanReadVals(vals)
                    newMove = move_obj.create(vals)
                    newMove.unit_factor = stock_move_id.unit_factor
                    self.updatePickOutMove(newMove, productionLocation, customerProductionLocation, workorderBrw, picking)
                elif stock_move_id.operation_type == 'deliver':
                    only_deliver_moves.append(stock_move_id)
            if only_deliver_moves:
                # Create picking to consume material delivered stock --> customer
                warehouse_production = productionBrws.location_dest_id.get_warehouse()
                stock_location = warehouse_production.lot_stock_id
                toCreate = self.getStockPickingOutVals(partner_id, stock_location, customerProductionLocation, productionBrws, origin, sub_workorder_id=workorderBrw.id)
                pick_out_2 = stock_piking.create(toCreate)
                for move in only_deliver_moves:
                    vals = move.read()[0]
                    self.cleanReadVals(vals)
                    stockMove = self.env['stock.move'].create(vals)
                    stockMove.unit_factor = move.unit_factor
                    self.updatePickOutMove(stockMove, stock_location, customerProductionLocation, workorderBrw, pick_out_2)
                out_picks.append(pick_out_2)
        return out_picks

    def updatePickOutMove(self, newMove, productionLocation, customerProductionLocation, workorderBrw, picking):
        newMove.state = 'draft'
        newMove.production_id = False
        newMove.mrp_original_move = False
        newMove.raw_material_production_id = False
        newMove.location_id = productionLocation.id
        newMove.location_dest_id = customerProductionLocation.id
        newMove.picking_id = picking.id
        newMove.workorder_id = workorderBrw.id
        newMove.mrp_workorder_id = workorderBrw.id
        
    def getStockPickingOutVals(self, partner_id, productionLocation, customerProductionLocation, productionBrws, origin, sub_workorder_id=False):
        return {'partner_id': partner_id.id,
                'location_id': productionLocation.id,
                'location_dest_id': customerProductionLocation.id,
                'min_date': datetime.datetime.now(),
                'move_type': 'direct',
                'picking_type_id': self.getPickingType(productionBrws),
                'origin': origin,
                'move_lines': [],
                'state': 'draft',
                'sub_contracting_operation': 'open',
                'sub_production_id': self.production_id.id,
                'sub_workorder_id': sub_workorder_id}

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

    @api.multi
    def create_vendors_from(self, partner_id):
        external_production_partner = self.env['external.production.partner']
        if partner_id:
            vals = {'partner_id': partner_id.id,
                    'price': 0.0,
                    'delay': 0.0,
                    'min_qty': 0.0,
                    'wizard_id': self.id
                    }
            return external_production_partner.create(vals)
        return external_production_partner

    @api.onchange('external_operation')
    def onchange_product_qty(self):
        raw_moves = []
        finished_moves = []
        if self.external_operation == 'parent':
            finished_moves = self.production_id.generateTmpFinishedMoves()
            raw_moves = self.production_id.generateTmpFinishedMoves()
        elif self.external_operation == 'operation':
            self.move_raw_ids = []
            self.move_finished_ids = []
            if self.work_order_id:
                r_moves = self.production_id.generateTmpRawMoves()
                for r_move in self.env["stock.tmp_move"].browse(r_moves):
                    for bom_line in self.production_id.bom_id.bom_line_ids:
                        if bom_line.operation_id == self.work_order_id.operation_id:
                            new_r_move = r_move.copy()
                            new_r_move.write({'product_id': bom_line.product_id.id,
                                              'product_uom_qty': bom_line.product_qty})
                            raw_moves.append(new_r_move.id)
                    break
                for r_move in self.env["stock.tmp_move"].browse(r_moves):
                    for bom_line in self.production_id.bom_id.bom_line_ids:
                        if bom_line.operation_id == self.work_order_id.operation_id:
                            new_r_move = r_move.copy()
                            new_r_move.write({'product_id': bom_line.product_id.id,
                                              'product_uom_qty': bom_line.product_qty})
                            finished_moves.append(new_r_move.id)
                    break
        else:
            finished_moves = self.production_id.generateTmpFinishedMoves()
            raw_moves = self.production_id.generateTmpRawMoves()
        self.move_raw_ids = raw_moves
        self.move_finished_ids = finished_moves
            
        

class TmpStockMove(models.Model):
    _name = "stock.tmp_move"
    _table = 'stock_tmp_move'
    _inherit = ['stock.move']

    unit_factor = fields.Float('Unit Factor', default=1)
    qty_available = fields.Float(_('Qty available'))
    location_available = fields.Many2one('stock.location', string=_('Qty Location'))
    external_prod_workorder_finish = fields.Many2one(comodel_name="mrp.workorder.externally.wizard",
                                                     string="Finished",
                                                     readonly=True)
    external_prod_raw = fields.Many2one(comodel_name="mrp.externally.wizard",
                                        string="Raw",
                                        readonly=True)
    external_prod_finish = fields.Many2one(comodel_name="mrp.externally.wizard",
                                           string="Finished",
                                           readonly=True)
    source_production_move = fields.Many2one(comodel_name="stock.move",
                                           string="Source Production move")
    operation_type = fields.Selection([
        ('deliver', _('Deliver')),
        ('deliver_consume', _('Deliver and Consume')),
        ],
        default='deliver_consume',
    )
    unit_factor_message = fields.Boolean(_('Unit Factor Message'))

    def _set_product_qty(self):
        # Don't remove, is used to overload product_qty check
        pass

    @api.onchange('operation_type')
    def changeOperationType(self):
        self.unit_factor_change()
        
    @api.onchange('unit_factor')
    def unit_factor_change(self):
        production_id = self.getProductionID()
        if self.external_prod_finish and production_id.product_id == self.product_id and self.unit_factor not in [1]:
            self.unit_factor = 1
            raise UserError(_('You cannot change quantity of manufactured product. Change manufacturing order quantity instead.'))
        if production_id and self.operation_type == 'deliver_consume':
            self.product_uom_qty = self.unit_factor * production_id.product_qty
        if self.source_production_move.unit_factor != self.unit_factor:
            self.unit_factor_message = True

    @api.onchange('product_uom_qty')
    def onchange_product_qty(self):
        self.unit_factor_change()

    @api.onchange('product_id')
    def onchange_product(self):
        if not self.product_id or self.product_qty < 0.0:
            self.product_qty = 0.0
        if self.product_id:
            self.location_dest_id = self.product_id.property_stock_production
            self.location_id = self.product_id.property_stock_production
            production_id = self.getProductionID()
            if production_id:
                self.origin = production_id.name

    def getWizard(self):
        wizard_id = self.env.context.get('wizard_obj_id', False)
        if wizard_id:
            wizard = self.env['mrp.externally.wizard'].browse(wizard_id)
            return wizard

    def getProductionID(self):
        wizard = self.getWizard()
        production_id = wizard.production_id
        if production_id:
            return production_id
#     @api.model
#     def default_get(self, fields_list):
#         context = self.env.context
#         res = super(TmpStockMove, self).default_get(fields_list)
#         wh = context.get('warehouse_id', False)
#         if wh:
#             res['warehouse_id'] = wh
#             res['name'] = self.env['stock.warehouse'].browse(res['warehouse_id']).display_name
#         wizardId = context.get('wizard_obj_id', False)
#         if wizardId:
#             wizardObj = self.env["mrp.externally.wizard"].browse(wizardId)
#             res['location_id'] = wizardObj.production_id.location_src_id.id
#         return res


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
