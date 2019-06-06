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
    work_order_id = fields.Many2one('mrp.workorder',
                                    string=_('Workorder'),
                                    readonly=True)
    request_date = fields.Datetime(string=_("Request date for the product"),
                                   default=lambda self: fields.datetime.now())
    create_purchese_order = fields.Boolean(_('Automatic create Purchase'), default=True)
    merge_purchese_order = fields.Boolean(_('Merge Purchase'), default=False)
    confirm_purchese_order = fields.Boolean(_('Confirm Purchase'), default=True)
    is_some_product = fields.Boolean(_('Same Product In and Out'), default=False)
    
    select_external_partner_ids = fields.Char(string=_('Select Partners'),
                                              compute='_compute_select_external_partner')
    select_external_partner = fields.Many2one('res.partner',
                                    string=_('External Partner Stock'))
    is_by_operation = fields.Boolean(default=False,
                                     string="Is computed by operation",
                                     help="""Push out and pull in only the product that have operation""")

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
        localStockLocation = productionBrws.product_id.property_stock_production    # Production location
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            customerProductionLocation = self.getCustomerLocation(partner_id)
            pickOut = self.createStockPickingOutProductionOrder(partner_id, productionBrws, customerProductionLocation, localStockLocation)
            pickIn = self.createStockPickingInProdOrder(partner_id, productionBrws, customerProductionLocation, localStockLocation, pickOut)
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pickOut.max_date
            if pickIn:
                pickingBrwsList.append(pickIn.id)
            if pickOut:
                pickingBrwsList.append(pickOut.id)
        self.createPurches(pickIn)
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
        return True

    def updateMOLinesWithDifferences(self, productionBrws):
        '''
            Update manufacturing order with quantities and products added / removed in the wizard
        '''
        firstRawMove = False
        for prod_raw_move in productionBrws.move_raw_ids:
            firstRawMove = prod_raw_move
        for raw_move in self.move_raw_ids:
            if raw_move.source_production_move:
                if raw_move.source_production_move.product_uom_qty != raw_move.product_uom_qty:
                    raw_move.source_production_move.product_uom_qty = raw_move.product_uom_qty
            else:
                firstRawMove.copy(self.getTmpMoveVals(raw_move))
        firstFinishMove = False
        for prod_finish_move in productionBrws.move_finished_ids:
            firstFinishMove = prod_finish_move
        for finish_move in self.move_finished_ids:
            if finish_move.source_production_move:
                if finish_move.source_production_move.product_uom_qty != finish_move.product_uom_qty:
                    finish_move.source_production_move.product_uom_qty = finish_move.product_uom_qty
            else:
                firstFinishMove.copy(self.getTmpMoveVals(finish_move))

    def getTmpMoveVals(self, tmp_move):
        return {
            'product_id': tmp_move.product_id.id,
            'product_uom_qty': tmp_move.product_uom_qty,
            'product_uom': tmp_move.product_uom.id,
            'name': tmp_move.name,
            'origin': tmp_move.origin,
            'date_expected': tmp_move.date_expected,
                    }

    @api.multi
    def setupOptions(self, workorderBrw):
        if workorderBrw.operation_id.external_operation == 'parent':
            self.is_some_product = True
            self.is_by_operation = False
        elif workorderBrw.operation_id.external_operation == 'operation':
            self.is_by_operation = True
            self.is_some_product = True
        elif workorderBrw.operation_id.external_operation == 'normal':
            self.is_by_operation = False
            self.is_some_product = False

    @api.multi
    def produce_workorder(self):
        workorderBrw = self.getParentObjectBrowse()
        productionBrws = workorderBrw.production_id
        self.checkCreateReorderRule(productionBrws)
        self.setupOptions(workorderBrw)
        localStockLocation = productionBrws.product_id.property_stock_production
        for external_partner in self.external_partner:
            if self.is_by_operation:
                pickOut, pickIn = self.getPicksByOperation(external_partner.partner_id, productionBrws, workorderBrw)
            else:
                partner_id = external_partner.partner_id
                customerProductionLocation = self.getCustomerLocation(partner_id)
                pickOut = self.createStockPickingOutWorkorder(partner_id, productionBrws, customerProductionLocation, localStockLocation, workorderBrw, self.is_some_product)
                pickIn = self.createStockPickingInWorkOrder(partner_id, productionBrws, customerProductionLocation, localStockLocation, workorderBrw, pickOut)
            date_planned_finished_wo = pickIn.max_date
            date_planned_start_wo = pickOut.max_date
        workorderBrw.date_planned_finished = date_planned_finished_wo
        workorderBrw.date_planned_start = date_planned_start_wo
        pickingBrwsList = [pickIn.id, pickOut.id]
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        self.createPurches(pickIn, workorderBrw)
        workorderBrw.state = 'external'
        self.updateMOLinesWithDifferences(productionBrws)

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
    def createPurches(self, pickIn, workorderBrws=False):
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
                purchaseBrws = purchaseOrderObj.create({'partner_id': toCreatePurchese.partner_id.id,
                                                        'date_planned': self.request_date,
                                                        'production_external_id': self.production_id.id})

            for lineBrws in pickIn.move_lines:
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

    def getOriginWorkOrder(self, productionBrws, originBrw):
        return "%s - %s - %s" % (productionBrws.name, originBrw.name, originBrw.external_partner.name)

    def createStockPickingInProdOrder(self, partner_id, productionBrws, customerProductionLocation, localStockLocation, pick_out=None):
        stock_piking = self.env['stock.picking']
        if not self.move_finished_ids:
            return stock_piking
        origin = self.getOriginProdOrder(productionBrws)
        toCreate = self.getStockPickingInVals(partner_id, customerProductionLocation, localStockLocation, productionBrws, pick_out, origin)
        obj = stock_piking.create(toCreate)
        for stock_move_id in self.move_finished_ids:
            vals = stock_move_id.read()[0]
            self.cleanReadVals(vals)
            stockMove = self.env['stock.move'].create(vals)
            stockMove.name = stock_move_id.product_id.display_name
            stockMove.location_id = customerProductionLocation.id
            stockMove.location_dest_id = localStockLocation.id
            stockMove.production_id = False
            stockMove.mrp_workorder_id = self.work_order_id.id
            stockMove.raw_material_production_id = False
            stockMove.picking_id = obj.id
            stockMove.state = 'draft'
        return obj

    def getStockPickingInVals(self, partner_id, customerProductionLocation, localStockLocation, productionBrws, pick_out, origin, sub_workorder_id=False):
        return {'partner_id': partner_id.id,
                'location_id': customerProductionLocation.id,
                'location_dest_id': localStockLocation.id,
                'min_date': productionBrws.date_planned_start,
                'move_type': 'direct',
                'picking_type_id': self.getPickingType(productionBrws, 'incoming'),
                'origin': origin,
                'move_lines': [],
                'state': 'draft',
                'sub_contracting_operation': 'close',
                'sub_production_id': self.production_id.id,
                'pick_out': pick_out.id,
                'sub_workorder_id': sub_workorder_id,
                }

    def createStockPickingInWorkOrder(self, partner_id, productionBrws, customerProductionLocation, localStockLocation, originBrw, pick_out=None):
        stock_piking = self.env['stock.picking']
        if not self.move_finished_ids:
            return stock_piking
        origin = self.getOriginWorkOrder(productionBrws, originBrw)
        toCreate = self.getStockPickingInVals(partner_id, customerProductionLocation, localStockLocation, productionBrws, pick_out, origin, originBrw.id)
        obj = stock_piking.create(toCreate)
        for tmpRow in self.move_finished_ids:
            vals = tmpRow.read()[0]
            self.cleanReadVals(vals)
            newMove = self.env['stock.move'].create(vals)
            newMove.location_id = customerProductionLocation.id
            newMove.location_dest_id = localStockLocation.id
            newMove.state = 'draft'
            newMove.production_id = False
            newMove.mrp_original_move = False
            newMove.raw_material_production_id = False
            newMove.picking_id = obj.id
        return obj

    def getIncomingTmpMoves(self, productionBrws, customerProductionLocation, partner_id):
        incomingMoves = []
        for productionLineBrws in productionBrws.move_finished_ids:
            if not customerProductionLocation:
                customerProductionLocation = productionLineBrws.location_id
            if productionLineBrws.state == 'confirmed' and productionLineBrws.partner_id == partner_id:
                incomingMoves.append(productionLineBrws)
        return incomingMoves

    def getCustomerLocation(self, partner_id):
        customerProductionLocation = partner_id.location_id
        if not customerProductionLocation:
            raise UserError(_('Partner %s has not location setup.' % (partner_id.name)))
        return customerProductionLocation

    def isWorkorder(self, originBrw):
        isWorkorder = False
        if originBrw:
            isWorkorder = originBrw._table == 'mrp_workorder'
        return isWorkorder

    def getPickingType(self, productionBrws, pick_type='outgoing'):
        warehouseId = productionBrws.picking_type_id.warehouse_id.id
        pickTypeObj = self.env['stock.picking.type']
        for pick in pickTypeObj.search([('code', '=', pick_type),
                                        ('active', '=', True),
                                        ('warehouse_id', '=', warehouseId)]):
            return pick.id
        return False

    def createStockPickingOutProductionOrder(self, partner_id, productionBrws, customerProductionLocation, localStockLocation):
        stock_piking = self.env['stock.picking']
        if not self.move_raw_ids:
            return stock_piking
        origin = self.getOriginProdOrder(productionBrws)
        toCreate = self.getStockPickingOutVals(partner_id, localStockLocation, customerProductionLocation, productionBrws, origin)
        obj = stock_piking.create(toCreate)
        for stock_move_id in self.move_raw_ids:
            vals = stock_move_id.read()[0]
            self.cleanReadVals(vals)
            stockMove = self.env['stock.move'].create(vals)
            stockMove.name = stock_move_id.product_id.display_name
            stockMove.unit_factor = stock_move_id.unit_factor
            stockMove.location_id = localStockLocation.id
            stockMove.location_dest_id = customerProductionLocation.id
            stockMove.picking_id = obj.id
            stockMove.state = 'draft'
        return obj

    

    def cleanReadVals(self, vals):
        for key, val in vals.items():
            if isinstance(val, tuple) and len(val) == 2:
                vals[key] = val[0]
        if 'product_qty' in vals:
            del vals['product_qty']

    def createStockPickingOutWorkorder(self, partner_id, productionBrws, customerProductionLocation, localStockLocation, originBrw, is_some_product=False):
        stock_piking = self.env['stock.picking']
        if not self.move_raw_ids:
            return stock_piking
        origin = self.getOriginWorkOrder(productionBrws, originBrw)
        toCreate = self.getStockPickingOutVals(partner_id, localStockLocation, customerProductionLocation, productionBrws, origin, sub_workorder_id=originBrw.id)
        obj = stock_piking.create(toCreate)
        if self.is_some_product and self.is_by_operation:   # Parent in - out
            for stock_move_id in self.move_finished_ids:
                vals = stock_move_id.read()[0]
                self.cleanReadVals(vals)
                newMove = self.env['stock.move'].create(vals)
                newMove.state = 'draft'
                newMove.production_id = False
                newMove.mrp_original_move = False
                newMove.raw_material_production_id = False
                newMove.location_id = localStockLocation.id
                newMove.location_dest_id = customerProductionLocation.id
                newMove.picking_id = obj.id
                # newMove.unit_factor = incomingTmpMove.unit_factor
        else:
            for stock_move_id in self.move_raw_ids:
                vals = stock_move_id.read()[0]
                self.cleanReadVals(vals)
                newMove = self.env['stock.move'].create(vals)
                newMove.state = 'draft'
                newMove.production_id = False
                newMove.mrp_original_move = False
                newMove.raw_material_production_id = False
                newMove.location_id = localStockLocation.id
                newMove.location_dest_id = customerProductionLocation.id
                newMove.picking_id = obj.id
        return obj

    def getStockPickingOutVals(self, partner_id, localStockLocation, customerProductionLocation, productionBrws, origin, sub_workorder_id=False):
        return {'partner_id': partner_id.id,
                'location_id': localStockLocation.id,
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
        vals = {'partner_id': partner_id.id,
                'price': 0.0,
                'delay': 0.0,
                'min_qty': 0.0,
                'wizard_id': self.id
                }
        return external_production_partner.create(vals)

    def updatePickIN(self, values, partner_id, localStockLocation, customerProductionLocation):
        """
            this function can be overloaded in order to customise the piking in
        """
        return values

    def updatePickOUT(self, values, partner_id, localStockLocation, customerProductionLocation):
        """
            this function can be overloaded in order to customise the piking out
        """
        return values

    def createStockPickingWorkorder(self,
                                    partner_id,
                                    mrp_production_id,
                                    mrp_workorder_id,
                                    products,
                                    location_id,
                                    location_dest_id,
                                    picking_type_str):
        def getPickingType(picking_type_str):
            warehouseId = mrp_production_id.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', picking_type_str),  # 'incoming', 'outgoing'
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        toCreate = {'partner_id': partner_id.id,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(picking_type_str),
                    'origin': self.getOriginWorkOrder(mrp_production_id, mrp_workorder_id),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'open',
                    'sub_production_id': self.production_id.id,
                    'sub_workorder_id': mrp_workorder_id.id}
        if picking_type_str == 'outgoing':
            toCreate = self.updatePickOUT(toCreate,
                                          partner_id,
                                          location_id,
                                          location_dest_id)
        else:
            toCreate = self.updatePickIN(toCreate,
                                         partner_id,
                                         location_id,
                                         location_dest_id)
        out_stock_picking_id = self.env['stock.picking'].create(toCreate)
        new_stock_move_line_ids = []
        for bom_line_id in products:
            vals = {'name': '',
                    'company_id': mrp_production_id.company_id.id,
                    'product_id': bom_line_id.product_id.id,
                    'product_uom_qty': bom_line_id.product_qty,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'state': 'draft',
                    'origin': "%s-%s" % (mrp_production_id, mrp_workorder_id.name),
                    'warehouse_id': mrp_production_id.picking_type_id.warehouse_id.id,
                    'production_id': False,
                    'mrp_production_id': False,
                    'product_uom': bom_line_id.product_uom_id.category_id.id,
                    'date_expected': self.request_date,
                    'mrp_original_move': False,
                    'workorder_id': mrp_workorder_id.id,
                    'mrp_workorder_id': mrp_workorder_id.id,
                    'unit_factor': 1,
                    'external_prod_workorder_finish': False,
                    'raw_material_production_id': False}
            new_stock_move_id = self.env['stock.move'].create(vals)
            new_stock_move_id.location_id = location_id.id
            new_stock_move_id.location_dest_id = location_dest_id.id
            new_stock_move_line_ids.append(new_stock_move_id.id)
        out_stock_picking_id.write({'move_lines': [(6, False, new_stock_move_line_ids)]})
        return out_stock_picking_id

    @api.model
    def getWorkorderProductsByOperation(self, mrp_production_id, mrp_workorder_id):
        out = []
        for bom_line_id in mrp_production_id.bom_id.bom_line_ids:
            if bom_line_id.operation_id == mrp_workorder_id.operation_id:
                out.append(bom_line_id)
        return out

    @api.model
    def getPicksByOperation(self, partner_id, mrp_production_id, mrp_workorder_id):
        location_dest_id = partner_id.location_id
        location_id = mrp_production_id.location_src_id
        products = self.getWorkorderProductsByOperation(mrp_production_id, mrp_workorder_id)
        stock_picking_in = self.createStockPickingWorkorder(partner_id,
                                                            mrp_production_id,
                                                            mrp_workorder_id,
                                                            products,
                                                            location_id,
                                                            location_dest_id,
                                                            picking_type_str='incoming')
        stock_picking_out = self.createStockPickingWorkorder(partner_id,
                                                             mrp_production_id,
                                                             mrp_workorder_id,
                                                             products,
                                                             location_dest_id,
                                                             location_id,
                                                             picking_type_str='outgoing')
        return stock_picking_in, stock_picking_out


class TmpStockMove(models.Model):
    _name = "stock.tmp_move"
    _table = 'stock_tmp_move'
    _inherit = ['stock.move']

    unit_factor = fields.Float('Unit Factor')
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

    def _set_product_qty(self):
        # Don't remove, is used to overload product_qty check
        pass

    @api.onchange('product_id', 'product_qty')
    def onchange_quantity(self):
        if not self.product_id or self.product_qty < 0.0:
            self.product_qty = 0.0
        if self.product_id:
            self.location_dest_id = self.product_id.property_stock_production
            self.location_id = self.product_id.property_stock_production
        wizard_id = self.env.context.get('wizard_obj_id', False)
        if wizard_id:
            wizard = self.env['mrp.externally.wizard'].browse(wizard_id)
            production_id = wizard.production_id
            if production_id:
                self.origin = production_id.name

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
