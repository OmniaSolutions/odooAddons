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
    unit_factor = fields.Float('Unit Factor')
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
    workorder_id = fields.Many2one(comodel_name='mrp.workorder', string='Workorder Id', readonly=True)

    qty_available = fields.Float(_('Qty available'))
    location_available = fields.Many2one('stock.location', string=_('Qty Location'))

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

    @api.onchange('consume_bom_id')
    def changeBOMId(self):
        self.operationTypeChanged()

    @api.multi
    def getWizardBrws(self):
        return self.browse(self._context.get('wizard_id', False))

    @api.onchange('operation_type')
    def operationTypeChanged(self):
        resObj = self.getParentObjectBrowse()
        if resObj._name == 'mrp.workorder':
            prodObj = resObj.production_id
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

    @api.multi
    def getParentObjectBrowse(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def cancelProductionRows(self, prodObj):
        for lineBrws in prodObj.move_raw_ids + prodObj.move_finished_ids:
            lineBrws.mrp_original_move = lineBrws.state
            lineBrws._action_cancel()

    def updateMoveLines(self, productionBrws):
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
                        'date_expected': fields.Datetime.from_string(self.request_date),
                        'mrp_production_id': productionBrws.id,
                        'unit_factor': lineBrws.unit_factor}
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
                    'date_expected': fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0),
                    'mrp_production_id': productionBrws.id,
                    'unit_factor': lineBrws.unit_factor
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

    @api.multi
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

    @api.multi
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No external partner set. Please provide one !!"))
        if not self.create_purchese_order and len(self.external_partner.ids) != 1:
            raise UserError(_("If you don't want to create purchase order you have to select only one partner."))

        productionBrws, workorderBrw = self.getWorkorderAndManufaturing()
        self.cancelProductionRows(productionBrws)
        self.updateMoveLines(productionBrws)
        date_planned_finished_wo = False
        date_planned_start_wo = False
        pickingBrwsList = []
        for external_partner in self.external_partner:
            partner_id = external_partner.partner_id
            pickOut = self.createStockPickingOut(partner_id, productionBrws)
            pickIn = self.createStockPickingIn(partner_id, productionBrws, workorderBrw, pick_out=pickOut)
            pickingBrwsList.extend((pickIn.id, pickOut.id))
            date_planned_finished_wo = pickIn.scheduled_date
            date_planned_start_wo = pickOut.scheduled_date
            self.createPurches(self.external_partner, pickIn, workorderBrw.id)
        productionBrws.date_planned_finished_wo = date_planned_finished_wo
        productionBrws.date_planned_start_wo = date_planned_start_wo
        productionBrws.external_pickings = [(6, 0, pickingBrwsList)]
        movesToCancel = productionBrws.move_raw_ids.filtered(lambda m: m.mrp_original_move is False)
        movesToCancel2 = productionBrws.move_finished_ids.filtered(lambda m: m.mrp_original_move is False)
        movesToCancel += movesToCancel2
        movesToCancel._do_unreserve()
        movesToCancel._action_cancel()

    @api.multi
    def createPurches(self, toCreatePurchese, picking, workorder):
        if not self.create_purchese_order:
            return
        obj_product_product = self.getDefaultExternalServiceProduct(workorder)
        obj_po = self.env['purchase.order'].create({'partner_id': toCreatePurchese.partner_id.id,
                                                    'date_planned': self.request_date,
                                                    'production_external_id': self.production_id.id,
                                                    'workorder_external_id': workorder,
                                                    })
        target_prod = False
        if workorder:
            wo_brws = self.env['mrp.workorder'].browse(workorder)
            target_prod = wo_brws.product_id.id
        else:
            target_prod = self.production_id.product_id.id
        for lineBrws in picking.move_lines:
            if lineBrws.product_id.id == target_prod or wo_brws.operation_id.external_operation == 'operation':
                values = {'product_id': obj_product_product.id,
                          'name': self.getPurcheseName(obj_product_product),
                          'product_qty': lineBrws.product_uom_qty,
                          'product_uom': obj_product_product.uom_po_id.id,
                          'price_unit': obj_product_product.price,
                          'date_planned': self.request_date,
                          'order_id': obj_po.id,
                          'production_external_id': self.production_id.id,
                          'workorder_external_id': workorder,
                          'sub_move_line': lineBrws.id,
                          }
                new_purchase_order_line = self.env['purchase.order.line'].create(values)
                new_purchase_order_line.onchange_product_id()
                new_purchase_order_line.date_planned = self.request_date
                new_purchase_order_line.product_qty = lineBrws.product_uom_qty
                lineBrws.purchase_order_line_subcontracting_id = new_purchase_order_line.id
                lineBrws.purchase_line_id = new_purchase_order_line
        if self.confirm_purchese_order:
            obj_po.button_confirm()

    @api.model
    def getNewExternalProductInfo(self, workorder_id=None):
        """
        this method could be overloaded as per customer needs
        """
        default_code = self.production_id.product_id.name
        if self.production_id.product_id.default_code:
            default_code = self.production_id.product_id.default_code
        new_default_code = "S-" + default_code
        new_name = "S-" + self.production_id.product_id.name
        if workorder_id:
            new_default_code = new_default_code + "-" + workorder_id.name
            new_name = new_name + "-" + workorder_id.name
        val = {'default_code': new_default_code,
               'type': 'service',
               'purchase_ok': True,
               'name': new_name}
        return val

    @api.model
    def getDefaultExternalServiceProduct(self, mrp_workorder_id=None):
        """
        get the default external product suitable for the purchase
        """
        if not mrp_workorder_id:
            return self.getDefaultProductionServiceProduct()
        else:
            return self.getDefaultWorkorderServiceProduct(mrp_workorder_id)

    @api.model
    def getDefaultProductionServiceProduct(self):
        """
        get the default external product suitable for the purchase
        """
        bom_product_product_id = self.production_id.bom_id.external_product
        if bom_product_product_id:
            return bom_product_product_id
        product_vals = self.getNewExternalProductInfo()
        newProduct = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
        if not newProduct:
            newProduct = self.env['product.product'].create(product_vals)
            newProduct.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                    message_type='notification')
        self.production_id.bom_id.external_product = newProduct
        return newProduct

    @api.model
    def getDefaultWorkorderServiceProduct(self, mrp_workorder_id=None):
        """
        get the default external product suitable for the purchase
        """
        mrp_workorder_id = self.env['mrp.workorder'].browse([mrp_workorder_id])
        if mrp_workorder_id.external_product:
            return mrp_workorder_id.external_product
        product_vals = self.getNewExternalProductInfo(mrp_workorder_id)
        newProduct = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
        if not newProduct:
            newProduct = self.env['product.product'].create(product_vals)
            newProduct.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                    message_type='notification')

        mrp_workorder_id.external_product = newProduct
        mrp_workorder_id.operation_id.external_product = newProduct
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

    @api.multi
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()

    def getOrigin(self, productionBrws, originBrw=None):
        return productionBrws.name

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

    def getIncomingTmpMoves(self, productionBrws, customerProductionLocation, partner_id, isWorkorder=False):
        incomingMoves = []
        lines = productionBrws.move_finished_ids
        if isWorkorder:
            lines = self.move_finished_ids
        for productionLineBrws in lines:
            if not customerProductionLocation:
                customerProductionLocation = productionLineBrws.location_id
            if productionLineBrws.state not in ['done', 'cancel']:  # and productionLineBrws.partner_id == partner_id:
                incomingMoves.append(productionLineBrws)
        return incomingMoves

    def createStockPickingIn(self, partner_id, productionBrws, originBrw=None, pick_out=None):

        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'incoming'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        isWorkorder = False
        if originBrw:
            isWorkorder = True
        stock_piking = self.env['stock.picking']
        if not pick_out:
            pick_out = stock_piking
        if not self.move_finished_ids:
            return stock_piking
        customerProductionLocation = partner_id.location_id
        if not customerProductionLocation:
            raise UserError(_('Partner %s has not location setup.' % (partner_id.name)))
        localStockLocation = productionBrws.location_src_id  # Taken from manufacturing order
        incomingMoves = self.getIncomingTmpMoves(productionBrws, customerProductionLocation, partner_id)
        toCreate = {'partner_id': partner_id.id,
                    'location_id': customerProductionLocation.id,
                    'location_dest_id': localStockLocation.id,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'close',
                    'sub_production_id': self.production_id.id,
                    'pick_out': pick_out.id}
        if originBrw and originBrw._table == 'mrp_workorder':  # Link picking with this workorder
            toCreate['sub_workorder_id'] = originBrw.id
        toCreate = self.updatePickIN(toCreate,
                                     partner_id,
                                     localStockLocation,
                                     customerProductionLocation)
        out_stock_picking_id = stock_piking.create(toCreate)
        newStockLines = []
        if isWorkorder:
            for stock_move_id in self.move_finished_ids:
                vals = {'name': stock_move_id.name,
                        'company_id': stock_move_id.company_id.id,
                        'product_id': stock_move_id.product_id.id,
                        'product_uom_qty': stock_move_id.product_uom_qty,
                        'location_id': stock_move_id.location_id.id,
                        'location_dest_id': stock_move_id.location_dest_id.id,
                        'note': stock_move_id.note,
                        'state': 'draft',
                        'origin': stock_move_id.origin,
                        'warehouse_id': stock_move_id.warehouse_id.id,
                        'production_id': False,
                        'product_uom': stock_move_id.product_uom.id,
                        'date_expected': stock_move_id.date_expected,
                        'mrp_original_move': False,
                        'workorder_id': originBrw.id if isWorkorder else stock_move_id.workorder_id.id,
                        'unit_factor': stock_move_id.unit_factor,
                        'raw_material_production_id': False}
                new_stock_move_id = self.env['stock.move'].create(vals)
                new_stock_move_id.location_id = customerProductionLocation.id
                new_stock_move_id.location_dest_id = localStockLocation.id
                newStockLines.append(new_stock_move_id.id)
#             for outGoingMove in incomingMoves:
#                 outGoingMove._action_cancel()
        else:
            for stock_move_id in incomingMoves:
                new_stock_move_id = stock_move_id.copy(default={'name': stock_move_id.product_id.display_name,
                                                                'location_id': customerProductionLocation.id,
                                                                'location_dest_id': localStockLocation.id,
                                                                'sale_line_id': stock_move_id.sale_line_id,
                                                                'production_id': False,
                                                                'mrp_workorder_id': originBrw.id if isWorkorder else self.workorder_id.id,
                                                                'raw_material_production_id': False,
                                                                'picking_id': out_stock_picking_id.id})
                newStockLines.append(new_stock_move_id.id)
                stock_move_id._action_cancel()
        productionBrws.createStockMoveBom()
        out_stock_picking_id.write({'move_lines': [(6, False, newStockLines)]})
        return out_stock_picking_id

    def createStockPickingOut(self, partner_id, mrp_production_id, originBrw=None, is_some_product=False):
        def getPickingType():
            warehouseId = mrp_production_id.picking_type_id.warehouse_id.id
            stock_picking_type = self.env['stock.picking.type']
            for stock_picking_type_id in stock_picking_type.search([('code', '=', 'outgoing'),
                                                                    ('active', '=', True),
                                                                    ('warehouse_id', '=', warehouseId)]):
                return stock_picking_type_id.id
            return False

        stock_picking = self.env['stock.picking']
        if not self.move_raw_ids:
            return stock_picking
        customerProductionLocation = partner_id.location_id
        if not customerProductionLocation:
            raise UserError(_('Partner %s has not location setup.' % (partner_id.name)))
        stock_location_id = mrp_production_id.location_src_id  # Taken from manufacturing order
        out_stock_move_ids = []
        isWorkorder = False
        if originBrw:
            isWorkorder = True
        if not is_some_product:
            stock_move_ids = mrp_production_id.move_raw_ids
        else:
            stock_move_ids = mrp_production_id.move_finished_ids
        for stock_move_id in stock_move_ids:
            if not customerProductionLocation:
                customerProductionLocation = stock_move_id.location_dest_id
            if stock_move_id.state not in ['done', 'cancel']:  # and stock_move_id.partner_id == partner_id:
                out_stock_move_ids.append(stock_move_id)
        toCreate = {'partner_id': partner_id.id,
                    'location_id': stock_location_id.id,
                    'location_dest_id': customerProductionLocation.id,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(mrp_production_id, originBrw),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'open',
                    'sub_production_id': self.production_id.id,
                    'mrp_workorder_id': originBrw.id if isWorkorder else self.workorder_id.id}
        if isWorkorder:
            toCreate['sub_workorder_id'] = originBrw.id
        toCreate = self.updatePickOUT(toCreate,
                                      partner_id,
                                      stock_location_id,
                                      customerProductionLocation)
        out_stock_picking_id = stock_picking.create(toCreate)
        new_stock_move_line_ids = []
        if isWorkorder:
            raw_moves = self.move_raw_ids
            if is_some_product:
                raw_moves = self.move_finished_ids
            for tmpRow in raw_moves:
                tmpRow
                vals = {'name': tmpRow.name,
                        'company_id': tmpRow.company_id.id,
                        'product_id': tmpRow.product_id.id,
                        'product_uom_qty': tmpRow.product_uom_qty,
                        'location_id': tmpRow.location_id.id,
                        'location_dest_id': tmpRow.location_dest_id.id,
                        'note': tmpRow.note,
                        'state': 'draft',
                        'origin': tmpRow.origin,
                        'warehouse_id': tmpRow.warehouse_id.id,
                        'production_id': False,
                        'product_uom': tmpRow.product_uom.id,
                        'date_expected': tmpRow.date_expected,
                        'mrp_original_move': False,
                        'workorder_id': originBrw.id if isWorkorder else tmpRow.workorder_id.id,
                        'unit_factor': tmpRow.unit_factor,
                        'external_prod_workorder_finish': False,
                        'raw_material_production_id': False}
                new_stock_move_id = self.env['stock.move'].create(vals)
                new_stock_move_id.location_id = stock_location_id.id
                new_stock_move_id.location_dest_id = customerProductionLocation.id
                new_stock_move_line_ids.append(new_stock_move_id.id)
            if not is_some_product:
                for outGoingMove in out_stock_move_ids:
                    outGoingMove._action_cancel()
        else:
            for stock_move_id in out_stock_move_ids:
                new_stock_move_id = stock_move_id.copy(default={'name': stock_move_id.product_id.display_name,
                                                                'production_id': False,
                                                                'mrp_workorder_id': self.workorder_id.id,
                                                                'raw_material_production_id': False,
                                                                'unit_factor': stock_move_id.unit_factor})
                new_stock_move_id.location_id = stock_location_id.id
                new_stock_move_id.location_dest_id = customerProductionLocation.id
                new_stock_move_id.sale_line_id = stock_move_id.sale_line_id.id
                new_stock_move_line_ids.append(new_stock_move_id.id)
        out_stock_picking_id.write({'move_lines': [(6, False, new_stock_move_line_ids)]})
        return out_stock_picking_id

    @api.multi
    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)

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


class externalWorkorderPartner(models.TransientModel):
    _name = 'external.workorder.partner'

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

    wizard_id = fields.Many2one('mrp.workorder.externally.wizard',
                                string="Vendors")


class MrpWorkorderWizard(MrpProductionWizard):
    _name = "mrp.workorder.externally.wizard"
    _inherit = ['mrp.production.externally.wizard']

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

    is_some_product = fields.Boolean(default=True,
                                     string="Some Product",
                                     help="Use same product for in and out picking")

    is_by_operation = fields.Boolean(default=False,
                                     string="Is computed by operation",
                                     help="""Push out and pull in only the product that have operation""")

    @api.multi
    def create_vendors_from(self, partner_id):
        external_production_partner = self.env['external.workorder.partner']
        vals = {'partner_id': partner_id.id,
                'price': 0.0,
                'delay': 0.0,
                'min_qty': 0.0,
                'wizard_id': self.id
                }
        return external_production_partner.create(vals)

    def createStockPickingWorkorder(self,
                                    partner_id,
                                    mrp_production_id,
                                    mrp_workorder_id,
                                    products,
                                    location_id,
                                    location_dest_id,
                                    picking_type_str):
        def getPickingType():
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
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(mrp_production_id, mrp_workorder_id),
                    'move_lines': [],
                    'state': 'draft',
                    'sub_contracting_operation': 'open',
                    'sub_production_id': self.production_id.id,
                    'mrp_workorder_id': mrp_workorder_id.id,
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
                    'product_uom_qty': bom_line_id.product_qty * mrp_production_id.product_qty,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'state': 'draft',
                    'origin': "%s-%s" % (mrp_production_id, mrp_workorder_id.name),
                    'warehouse_id': mrp_production_id.picking_type_id.warehouse_id.id,
                    'production_id': False,
                    'product_uom': bom_line_id.product_uom_id.category_id.id,
                    'date_expected': self.request_date,
                    'mrp_original_move': False,
                    'workorder_id': mrp_workorder_id.id,
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
                                                            location_dest_id,
                                                            location_id,
                                                            picking_type_str='incoming')
        stock_picking_out = self.createStockPickingWorkorder(partner_id,
                                                             mrp_production_id,
                                                             mrp_workorder_id,
                                                             products,
                                                             location_id,
                                                             location_dest_id,
                                                             picking_type_str='outgoing')
        return stock_picking_in, stock_picking_out

    @api.multi
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No partner selected"))
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        mrp_workorder_id = relObj.browse(objIds)
        mrp_workorder_id.write({'external_partner': self.external_partner.partner_id.id,
                                'state': 'external'})
        # this is in case of automatic operation
        if mrp_workorder_id.operation_id.external_operation == 'parent':
            self.is_some_product = True
            self.is_by_operation = False
        elif mrp_workorder_id.operation_id.external_operation == 'operation':
            self.is_by_operation = True
            self.is_some_product = True
        elif mrp_workorder_id.operation_id.external_operation == 'normal':
            self.is_by_operation = False
            self.is_some_product = False
        #
        mrp_production_id = mrp_workorder_id.production_id
        for external_partner in self.external_partner:
            if self.is_by_operation:
                pickOut, pickIn = self.getPicksByOperation(external_partner.partner_id, mrp_production_id, mrp_workorder_id)
            else:
                pickOut = self.createStockPickingOut(external_partner.partner_id, mrp_production_id, mrp_workorder_id, self.is_some_product)
                pickIn = self.createStockPickingIn(external_partner.partner_id, mrp_production_id, mrp_workorder_id, pick_out=pickOut)
        if pickIn:
            mrp_production_id.date_planned_finished_wo = pickIn.scheduled_date
            self.createPurches(self.external_partner, pickIn, mrp_workorder_id.id)
        if pickOut:
            mrp_production_id.date_planned_start_wo = pickOut.scheduled_date
        mrp_production_id.button_unreserve()   # Needed to evaluate picking out move

    def getOrigin(self, productionBrws, originBrw):
        return "%s - %s - %s" % (productionBrws.name, originBrw.name, originBrw.external_partner.name)
