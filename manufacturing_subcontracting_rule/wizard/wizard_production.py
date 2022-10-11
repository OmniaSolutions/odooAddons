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
    is_dropship = fields.Boolean(string=_('Is Dropship'))
    parent_in_out = fields.Boolean(string=_('Partner In - Out'))

    @api.model
    def _service_product(self):
        self.service_product_to_buy = self.getDefaultProductionServiceProduct()

    @api.onchange('external_partner')
    def changeExternalPartner(self, external_partner_model='external.production.partner', raw_moves=False, finished_moves=False, ext_partner=False):
        ext_partners, raw_moves, finished_moves = self._changeExternalPartner(external_partner_model, raw_moves, finished_moves, ext_partner)
        self.external_partner = ext_partners
        
    def _changeExternalPartner(self, external_partner_model='external.production.partner', raw_moves=False, finished_moves=False, ext_partner=False):
        active_partners = self.env['res.partner']
        ext_partners = self.env[external_partner_model]
        if not raw_moves:
            raw_moves = self.move_raw_ids
        if not finished_moves:
            finished_moves = self.move_finished_ids
        if not ext_partner:
            ext_partner = self.external_partner
        for partner_suppl_info in ext_partner:
            ext_partners += partner_suppl_info
            partner_id = partner_suppl_info.partner_id
            active_partners += partner_id
            partner_location_id = self.getPartnerLocation(partner_id)
            if len(ext_partner) == 1:
                raw_moves.location_dest_id = partner_location_id.id
                raw_moves.location_id = self.production_id.location_src_id.id
                for move_raw in raw_moves:
                    if not move_raw.partner_id:
                        move_raw.partner_id = partner_id.id
                finished_moves.location_dest_id = self.production_id.location_src_id
                finished_moves.location_id = partner_location_id
                for finish_move in finished_moves:
                    if not finish_move.partner_id:
                        finish_move.partner_id = partner_id.id
            else:
                existing_raw_moves = raw_moves.filtered(lambda x:x.partner_id.id == partner_id.id)
                if not existing_raw_moves:
                    partner_ids = raw_moves.mapped('partner_id')
                    if not partner_ids:
                        raw_moves.location_dest_id = partner_location_id.id
                        raw_moves.location_id = self.production_id.location_src_id.id
                        raw_moves.partner_id = partner_id.id
                        finished_moves.location_dest_id = self.production_id.location_src_id
                        finished_moves.location_id = partner_location_id
                        finished_moves.partner_id = partner_id.id
                    for partner in partner_ids:
                        if partner != partner_id:
                            for move_raw in raw_moves.filtered(lambda x:x.partner_id.id == partner.id):
                                new_raw_move = move_raw.copy()
                                new_raw_move.location_dest_id = partner_location_id
                                new_raw_move.location_id = self.production_id.location_src_id
                                new_raw_move.partner_id = partner_id.id
                            for finish_move in finished_moves.filtered(lambda x:x.partner_id.id == partner.id):
                                new_finish_move = finish_move.copy()
                                new_finish_move.location_dest_id = self.production_id.location_src_id
                                new_finish_move.location_id = partner_location_id
                                new_finish_move.partner_id = partner_id.id
                        break
        if active_partners:
            for line in raw_moves:
                if line.partner_id not in active_partners:
                    line.unlink()
            for line in finished_moves:
                if line.partner_id not in active_partners:
                    line.unlink()
        return ext_partners, raw_moves, finished_moves

    @api.onchange('is_dropship')
    def change_is_dropship(self):
        ext_partners = self.external_partner.sorted('sequence')
        if self.is_dropship:
            for line in self.move_raw_ids:
                if line.partner_id != ext_partners[0].partner_id:
                    line.unlink()
            for line in self.move_finished_ids:
                if line.partner_id != ext_partners[-1].partner_id:
                    line.unlink()
        else:
            wizard_values = self.production_id.get_wizard_value()
            self.write({
                'move_raw_ids': wizard_values.get('move_raw_ids', []),
                'move_finished_ids': wizard_values.get('move_finished_ids', [])
                })
            self.move_finished_ids.partner_id = ext_partners[0].partner_id
            self.changeExternalPartner()
            self._request_date()

    @api.onchange('request_date')
    def _request_date(self):
        for move in self.move_raw_ids:
            product_delay = move.product_id.produce_delay
            move.date_expected = fields.Datetime.from_string(self.request_date) - relativedelta(days=product_delay or 0.0)
        for move in self.move_finished_ids:
            move.date_expected = self.request_date

    def getWizardBrws(self):
        return self.browse(self._context.get('wizard_id', False))
    
    def getParentObjectBrowse(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        return relObj.browse(objIds)

    def cancelProductionRows(self, prodObj):
        '''
            Don't unify these for loops! _action_cancel do cancel of finished moves before to set mrp_original_move field.
            In case of cancel manufacturin order it causes unable to complete MO!
        '''
        for lineBrws in prodObj.move_raw_ids + prodObj.move_finished_ids:
            lineBrws.mrp_original_move = lineBrws.state
        for lineBrws in prodObj.move_raw_ids + prodObj.move_finished_ids:
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

    def generateDropship(self, ext_partners, productionBrws):
        pickingBrwsList = self.env['stock.picking']
        next_dropship = self.env['stock.picking']
        date_planned_start = False
        date_planned_finished = False
        ext_partners = ext_partners.sorted('sequence', reverse=True)
        next_partner = self.env['res.partner']
        for external_partner in ext_partners:
            partner_id = external_partner.partner_id
            if external_partner == ext_partners[0]:
                next_dropship = self.createStockPickingIn(partner_id, productionBrws)
                pickingBrwsList += next_dropship
                date_planned_finished = next_dropship.scheduled_date
                self.createPurchase(external_partner, next_dropship)
            elif external_partner == ext_partners[-1]:
                pick_out = self.createStockPickingOut(partner_id, productionBrws)
                pickingBrwsList += pick_out
                date_planned_start = pick_out.scheduled_date
            if external_partner != ext_partners[0]:
                next_dropship = self.createDropship(partner_id, next_partner, productionBrws, next_dropship)
                pickingBrwsList += next_dropship
                if external_partner != ext_partners[-1]:
                    self.createPurchase(external_partner, next_dropship)
                if external_partner == ext_partners[-1]:
                    pick_out.dropship_pick = next_dropship.id
                    self.createPurchase(external_partner, next_dropship)
            next_partner = partner_id
        return pickingBrwsList.ids, date_planned_start, date_planned_finished
    
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
        if self.is_dropship:
            pickingBrwsList, date_planned_start, date_planned_finished = self.generateDropship(self.external_partner, productionBrws)
        else:
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

    def getExisistingPO(self, purchase_vals):
        purchase = self.env['purchase.order']
        purchase_ids = purchase.search([
            ('partner_id', '=', purchase_vals['partner_id']),
            ('state', '=', 'draft')
            ], order='id DESC', limit=1)
        return purchase_ids

    def getPo(self, purchase_vals):
        obj_po = self.env['purchase.order']
        if self.merge_purchese_order:
            obj_po = self.getExisistingPO(purchase_vals)
        if not obj_po:
            obj_po = obj_po.create(purchase_vals)
        return obj_po

    def createPurchase(self, external_partner, picking):
        if not self.create_purchese_order:
            return 
        obj_product_product = self.getDefaultProductionServiceProduct()
        purchase_vals = self.getPurchaseVals(external_partner)
        obj_po = self.getPo(purchase_vals)
        for lineBrws in picking.move_lines:
            self.setupSupplierinfo(obj_product_product)
            values = self.getPurchaseLineVals(obj_product_product, obj_po, lineBrws)
            new_purchase_order_line = self.env['purchase.order.line'].create(values)
            new_purchase_order_line.onchange_product_id()
            new_purchase_order_line.date_planned = self.request_date
            new_purchase_order_line.product_qty = lineBrws.product_uom_qty
            lineBrws.purchase_order_line_subcontracting_id = new_purchase_order_line.id
            lineBrws.purchase_line_id = new_purchase_order_line
            new_purchase_order_line.move_ids = lineBrws
        if self.confirm_purchese_order and len(self.external_partner) == 1:
            obj_po.button_confirm()
            for po_line in obj_po.order_line:
                for move in po_line.move_ids:
                    if move.product_id == po_line.product_id:
                        move._action_cancel()
                        move.unlink()
        obj_po._compute_picking()
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
            default_code = product_vals.get('default_code')
            bom_product_product_id = self.env['product.product'].search([('default_code', '=', default_code)])
            if not bom_product_product_id:
                bom_product_product_id = self.env['product.product'].create(product_vals)
                bom_product_product_id.type = 'service'
                bom_product_product_id.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                        message_type='notification')
            elif len(bom_product_product_id) > 1:
                raise UserError('You have more than one product with default code %r' % (default_code))
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
        if picking_type == 'dropship':
            return self.env.ref('stock_dropshipping.picking_type_dropship').id
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
        elif operation_type == 'incoming':
            location_dest_id = mrp_production_id.location_src_id
            location_id = self.getPartnerLocation(partner_id)
        elif operation_type == 'subcontracting_out':
            operation_type = 'outgoing'
            location_dest_id = subcontract_loc
            location_id = self.getPartnerLocation(partner_id)
        elif operation_type == 'subcontracting_in':
            operation_type = 'incoming'
            location_dest_id = self.getPartnerLocation(partner_id)
            location_id = subcontract_loc
        elif operation_type == 'dropship':
            operation_type = 'dropship'
            location_dest_id = self.getPartnerLocation(partner_id)
            location_id = subcontract_loc
        vals = {
            'partner_id': partner_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'move_type': 'direct',
            'picking_type_id': self.getPickingType(mrp_production_id, operation_type),
            'origin': self.getOrigin(mrp_production_id),
            'move_lines': [],
            'state': 'draft',
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

    def createDropship(self, partner_from_id, partner_to_id, mrp_production_id, next_dropship):
        stock_picking = self.env['stock.picking']
        if not self.move_finished_ids or not self.move_finished_ids.filtered(lambda x: x.product_uom_qty > 0):
            return stock_picking
        partner_from_location = self.getPartnerLocation(partner_from_id)
        partner_to_location = self.getPartnerLocation(partner_to_id)
        picking_vals = self.getPickingVals(partner_from_id, mrp_production_id, 'dropship')
        picking_vals['location_id'] = partner_from_location.id
        picking_vals['location_dest_id'] = partner_to_location.id
        picking_vals['dropship_pick'] = next_dropship.id
        out_stock_picking_id = stock_picking.create(picking_vals)
        stock_move_ids = self.move_finished_ids
        out_stock_move_ids = stock_move_ids.filtered(lambda x: x.state not in ['done', 'cancel'])
        for stock_move_id in out_stock_move_ids.filtered(lambda x: x.partner_id.id == partner_from_id.id):
            new_stock_move_id = self.env['stock.move']
            stock_move_vals = self.getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, partner_from_location, partner_to_location)
            new_stock_move_id = new_stock_move_id.create(stock_move_vals)
        return out_stock_picking_id

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
        logging.info('Subcontracting create stock picking out with out_stock_move_ids %r partner_id %r out_stock_move_ids mapped %r' % (out_stock_move_ids, partner_id, out_stock_move_ids.mapped('partner_id')))
        for stock_move_id in out_stock_move_ids.filtered(lambda x: x.partner_id.id == partner_id.id):
            logging.info('Subcontracting create stock picking out 2 with stock_move_id %r' % (stock_move_id))
            new_stock_move_id = self.env['stock.move']
            stock_move_vals = self.getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, stock_location_id, customerProductionLocation)
            new_stock_move_id = new_stock_move_id.create(stock_move_vals)
            if cancel_source_moves:
                mrp_production_id.move_raw_ids._action_cancel()
        return out_stock_picking_id

    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)

    
    def create_vendors(self):
        external_production_partner = self.env['external.production.partner']
        sequence = 10
        for seller in self.consume_bom_id.external_product.seller_ids:
            vals = {'partner_id': seller.name.id,
                    'price': seller.price,
                    'delay': seller.delay,
                    'min_qty': seller.min_qty,
                    'wizard_id': self.id,
                    'sequence': sequence,
                    }
            sequence += 10
            external_production_partner.create(vals)
        self.changeExternalPartner()
