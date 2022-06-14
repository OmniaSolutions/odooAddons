'''
Created on 16 May 2022

@author: dsmerghetto
'''
import logging
import odoo
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tests import SavepointCase


#@odoo.tests.tagged('-standard', 'manufacturing_subcontracting_rule')
#@odoo.tests.tagged('post_install','-at_install')
class TestSubcontracting(TransactionCase):

    def setUp(self):
        self.test_01 = False
        self.test_02 = False
        self.test_03 = False
        self.test_04 = False
        self.test_05 = False
        self.test_06 = False
        self.test_07 = False
        self.test_08 = False
        self.test_09 = False
        self.test_10 = False
        self.test_11 = True
        super(TestSubcontracting, self).setUp()

    def createProduction(self, finish_qty=1):
        production_env = self.env['mrp.production']
        production_form = Form(production_env)
        production_form.product_id = self.finished
        production_form.bom_id = self.test_bom
        production_form.product_qty = finish_qty
        self.test_production = production_form.save()
        self.stock_location = self.test_production.location_src_id

    def createSubcontractLocation(self, name):
        location_env = self.env['stock.location']
        return location_env.create({
            'name': name,
            'usage': 'customer',
            })

    def createSubcontractLocation1(self):
        self.subcontract_loc_1 = self.createSubcontractLocation('Test Subcontract Loc 1')
        return self.subcontract_loc_1

    def createSubcontractLocation2(self):
        self.subcontract_loc_2 = self.createSubcontractLocation('Test Subcontract Loc 2')
        return self.subcontract_loc_2

    def createSubcontractLocation3(self):
        self.subcontract_loc_3 = self.createSubcontractLocation('Test Subcontract Loc 3')
        return self.subcontract_loc_3

    def createExternalPartner(self, partner_name, subcontract_location):
        partner_env = self.env['res.partner']
        external_partner_form = Form(partner_env)
        try:
            external_partner_form.name = partner_name
        except:
            firstname, lastname = partner_name.split(' ')
            external_partner_form.firstname = firstname
            external_partner_form.lastname = lastname
        external_partner_form.location_id = subcontract_location
        return external_partner_form.save()

    def createExternalPartner1(self):
        self.external_partner1 = self.createExternalPartner('Test Supplier1', self.subcontract_loc_1)
        return self.external_partner1

    def createExternalPartner2(self):
        self.external_partner2 = self.createExternalPartner('Test Supplier2', self.subcontract_loc_2)
        return self.external_partner2

    def createExternalPartner3(self):
        self.external_partner3 = self.createExternalPartner('Test Supplier3', self.subcontract_loc_3)
        return self.external_partner3

    def createProducts(self):
        prod_env = self.env['product.product']
        self.raw_1 = prod_env.create({
            'name': 'Raw Prod 1',
            'purchase_ok': True,
            'type': 'product',
            })
        self.raw_2 = prod_env.create({
            'name': 'Raw Prod 2',
            'purchase_ok': True,
            'type': 'product',
            })
        self.finished = prod_env.create({
            'name': 'Finish Prod 1',
            'purchase_ok': True,
            'can_be_produced': True,
            'type': 'product',
            })
        self.finished_service = prod_env.create({
            'name': 'S-Finish Prod 1 Service',
            'purchase_ok': True,
            'can_be_produced': False,
            'type': 'service',
            })

    def createBom(self):
        bom_env = self.env['mrp.bom']
        bom_line_env = self.env['mrp.bom.line']
        self.test_bom = bom_env.create({
                    'product_id': self.finished.id,
                    'product_tmpl_id': self.finished.product_tmpl_id.id,
                    'product_uom_id': self.finished.uom_id.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                    'external_product': self.finished_service.id,
                })
        self.test_bom_line1 = bom_line_env.create({
            'bom_id': self.test_bom.id,
            'product_id': self.raw_1.id,
            'product_qty': 2,
        })
        self.test_bom_line2 = bom_line_env.create({
            'bom_id': self.test_bom.id,
            'product_id': self.raw_2.id,
            'product_qty': 5,
        })

    def createOperations(self, bom_id, partner):
        routing_workcenter = self.env['mrp.routing.workcenter']
        self.op1 = routing_workcenter.create({
            'name': 'op1',
            'workcenter_id': 1,
            'default_supplier': partner.id,
            'bom_id': bom_id.id,
            })
        self.op2 = routing_workcenter.create({
            'name': 'op2',
            'workcenter_id': 1,
            'default_supplier': partner.id,
            'bom_id': bom_id.id,
            })

    def setupConsumedInOperation(self, bom_line, operation):
        bom_line.operation_id = operation.id

    def createSupplierInfo(self, partner):
        supplierinfo = self.env['product.supplierinfo']
        self.finished_supplierinfo_1 = supplierinfo.create({
            'name': partner.id,
            'product_tmpl_id': self.finished_service.product_tmpl_id.id,
            'product_id': self.finished_service.id,
            })

    def createSupplierInfo1(self):
        self.finished_supplierinfo_1 = self.createSupplierInfo(self.external_partner1)

    def createSupplierInfo2(self):
        self.finished_supplierinfo_2 = self.createSupplierInfo(self.external_partner2)

    def updateStartingStockQty(self, product, location, qty):
        stock_quant_model = self.env['stock.quant']
        stock_quant_model.create({
            'location_id': location.id,
            'product_id': product.id,
            'quantity': qty,
            })

    def checkQuantQty(self, product, location, expected_qty, pick_type):
        stock_quant_model = self.env['stock.quant']
        stock_quants = stock_quant_model.search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
            ])
        for quant in stock_quants:
            if quant.quantity != expected_qty:
                raise Exception('Wrong qty after picking %s' % (pick_type))
        if not stock_quants:
            raise Exception('No quants found.')

    def execProduceExternallyMO(self, production):
        vals = production.button_produce_externally()
        model = vals.get('res_model', '')
        res_id = vals.get('res_id', False)
        ext_wizard = self.env[model].browse(res_id)
        ext_wizard = ext_wizard.with_context({
            'active_model': production._name,
            'active_ids': production.id,
            })
        return ext_wizard

    def execProduceExternallyWO(self, workorder):
        vals = workorder.button_produce_externally()
        model = vals.get('res_model', '')
        res_id = vals.get('res_id', False)
        ext_wizard = self.env[model].browse(res_id)
        ext_wizard = ext_wizard.with_context({
            'active_model': workorder._name,
            'active_ids': workorder.id,
            })
        return ext_wizard

    def getExtPickings(self, production, partner_id=False):
        ext_picks = production.getExtPickIds()
        if not ext_picks:
            raise Exception('No pickings created')
        
        manufacture_type = self.env.ref('mrp.picking_type_manufacturing')
        incoming_type = self.env.ref('stock.picking_type_in')
        internal_type = self.env.ref('stock.picking_type_internal')
        outgoing_type = self.env.ref('stock.picking_type_out')
        dropship_type = self.env.ref('stock_dropshipping.picking_type_dropship')
        out_pick = self.env['stock.picking']
        in_pick = self.env['stock.picking']
        manuf_pick = self.env['stock.picking']
        dropship_pick = self.env['stock.picking']
        internal_pick = self.env['stock.picking']
        for pick in ext_picks:
            if pick.picking_type_id == outgoing_type:
                if partner_id and pick.partner_id == partner_id:
                    out_pick += pick
                else:
                    out_pick += pick
            elif pick.picking_type_id == incoming_type:
                if partner_id and pick.partner_id == partner_id:
                    in_pick += pick
                else:
                    in_pick += pick
            elif pick.picking_type_id == manufacture_type:
                if partner_id and pick.partner_id == partner_id:
                    manuf_pick += pick
                else:
                    manuf_pick += pick
            elif pick.picking_type_id == dropship_type:
                if partner_id and pick.partner_id == partner_id:
                    dropship_pick += pick
                else:
                    dropship_pick += pick
            elif pick.picking_type_id == internal_type:
                if partner_id and pick.partner_id == partner_id:
                    internal_pick += pick
                else:
                    internal_pick += pick
        if not out_pick:
            raise Exception('Out picking not created')
        if not in_pick:
            raise Exception('In picking not created')
        return out_pick, in_pick, manuf_pick, dropship_pick, internal_pick

    def validatePicking(self, pick, force_qty=False):
        pick.action_confirm()
        pick.action_assign()
        if force_qty:
            for line in pick.move_line_ids_without_package:
                line.qty_done = force_qty
        res = pick.button_validate()
        if isinstance(res, dict) and res['res_model'] == 'stock.immediate.transfer':
            immediate_transfer_form = Form(self.env[res['res_model']].with_context(res['context']))
            immediate_transfer = immediate_transfer_form.save()
            immediate_transfer.process()
        if isinstance(res, dict) and res['res_model'] == 'stock.backorder.confirmation':
            immediate_transfer_form = Form(self.env[res['res_model']].with_context(res['context']))
            immediate_transfer = immediate_transfer_form.save()
            immediate_transfer.process()

    def cancelMo(self, production):
        production.button_cancel_produce_externally()

    def cancelWo(self, workorder):
        workorder.button_cancel_produce_externally()

    def createTmpStockMove(self, name, product_id, qty, location_id, location_dest_id, partner_id, origin, production_id, external_prod_raw, external_prod_finish, product_uom,obj='mrp.production'):
        tmp_move_env = self.env["stock.tmp_move"]
        target_raw_field = 'external_prod_raw'
        target_finish_field = 'external_prod_finish'
        if obj == 'mrp.workorder':
            target_raw_field = 'external_prod_workorder_raw'
            target_finish_field = 'external_prod_workorder_finish'
        vals = {
            'name': name,
            'product_id': product_id.id,
            'product_uom_qty': qty,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': partner_id.id,
            'origin': origin,
            'production_id': production_id.id,
            target_raw_field: external_prod_raw.id,
            target_finish_field: external_prod_finish.id,
            'product_uom': product_uom.id,
            }
        return tmp_move_env.create(vals)

    def getPurchase(self, partner_id, production_id=False, workorder_id=False):
        to_filter = []
        if production_id:
            to_filter.append(('production_external_id', '=', production_id.id))
        elif workorder_id:
            to_filter.append(('workorder_external_id', '=', workorder_id.id))
        if partner_id:
            to_filter.append(('partner_id', '=', partner_id.id))
        purchase_ids = self.env['purchase.order'].search(to_filter)
        return purchase_ids

    def checkPurchase(self, purchase_ids, finished_to_produce):
        if len(purchase_ids) != 1:
            raise Exception('Wrong number of purchase')
        products = {}
        purchase_lines = purchase_ids.order_line
        for line in purchase_lines:
            products.setdefault(line.product_id, 0)
            products[line.product_id] += line.product_uom_qty
        if len(products.keys()) != 1:
            raise Exception('Wrong number of purchase lines')
        for qty in products.values():
            if qty != finished_to_produce:
                raise Exception('Wrong qty to purchase')

    def getWorkorders(self, production, op1, op2):
        wo_raw_1 = self.env['mrp.workorder']
        wo_raw_2 = self.env['mrp.workorder']
        for wo in production.workorder_ids:
            if wo.operation_id == op1:
                wo_raw_1 = wo
            elif wo.operation_id == op2:
                wo_raw_2 = wo
        return wo_raw_1, wo_raw_2

    def test_01_subcontracting_simple_1(self):
        logging.info('Start test_01_subcontracting_simple_1.')
        if self.test_01:
            finished_to_produce = 1
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 2, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 5, 'out')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_1, self.stock_location, 998, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 995, 'in')
            self.checkQuantQty(self.finished, self.stock_location, finished_to_produce, 'in')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, finished_to_produce)
            logging.info('End test_01_subcontracting_simple_1.')
        self.assertEqual(1, 1)
    
    def test_02_subcontracting_send_more(self):
        logging.info('Start test_02_subcontracting_send_more.')
        if self.test_02:
            finished_to_produce = 1
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            qty_delivered_extra = 10
            self.createTmpStockMove('Deliver %r X %r' % (self.raw_2.display_name, qty_delivered_extra), 
                                    self.raw_2, 
                                    qty_delivered_extra, 
                                    self.stock_location, 
                                    self.subcontract_loc_1, 
                                    self.external_partner1, 
                                    self.test_production.name, 
                                    self.test_production, 
                                    ext_wizard, 
                                    self.env["mrp.production.externally.wizard"],
                                    self.raw_2.uom_id)
            self.createTmpStockMove('Get %r X %r' % (self.finished.display_name, qty_delivered_extra), 
                                    self.finished, 
                                    5, 
                                    self.subcontract_loc_1, 
                                    self.stock_location, 
                                    self.external_partner1, 
                                    self.test_production.name, 
                                    self.test_production, 
                                    self.env["mrp.production.externally.wizard"],
                                    ext_wizard, 
                                    self.finished.uom_id)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 2, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, -10, 'in')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, -15, 'in')
            self.checkQuantQty(self.raw_1, self.stock_location, 998, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            self.checkQuantQty(self.finished, self.stock_location, 6, 'in')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, 6)
        logging.info('End test_02_subcontracting_send_more.')
        self.assertEqual(1, 1)
    
    def test_03_subcontracting_receive_less(self):
        logging.info('Start test_04_subcontracting_receive_less.')
        if self.test_03:
            finished_to_produce = 3
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            for move in ext_wizard.move_finished_ids:
                move.product_uom_qty = 2 # 3
            for move in ext_wizard.move_raw_ids:
                if move.product_id == self.raw_1:
                    move.product_uom_qty = 1 # 2
                if move.product_id == self.raw_2:
                    move.product_uom_qty = 3 # 5
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 1, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 3, 'out')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, -3, 'in')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, -7, 'in')
            self.checkQuantQty(self.raw_1, self.stock_location, 999, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 997, 'in')
            self.checkQuantQty(self.finished, self.stock_location, 2, 'in')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, 2)
        logging.info('End test_04_subcontracting_receive_less.')
        self.assertEqual(1, 1)
    
    def test_04_subcontracting_workorder(self):
        logging.info('Start test_05_subcontracting_workorder.')
        if self.test_04:
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createOperations(self.test_bom, self.external_partner1)
            self.setupConsumedInOperation(self.test_bom_line1, self.op1)
            self.setupConsumedInOperation(self.test_bom_line2, self.op2)
            self.createSupplierInfo1()
            self.createProduction(3)
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            wo_raw_1 = self.env['mrp.workorder']
            wo_raw_2 = self.env['mrp.workorder']
            for wo in self.test_production.workorder_ids:
                if wo.operation_id == self.op1:
                    wo_raw_1 = wo
                elif wo.operation_id == self.op2:
                    wo_raw_2 = wo
            ext_wizard = self.execProduceExternallyWO(wo_raw_1)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'out')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 1000, 'out')
            ext_wizard = self.execProduceExternallyWO(wo_raw_2)
            ext_wizard.button_produce_externally()
            out_pick_2, in_pick_2, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick_2 - out_pick)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'out')
            self.validatePicking(in_pick_2 - in_pick)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 1000, 'out')
        
            purchase_ids = self.getPurchase(self.external_partner1, False, wo_raw_1)
            self.checkPurchase(purchase_ids, 6)
            purchase_ids = self.getPurchase(self.external_partner1, False, wo_raw_2)
            self.checkPurchase(purchase_ids, 15)
        logging.info('End test_05_subcontracting_workorder.')
        self.assertEqual(1, 1)
    
    def test_05_subcontracting_workorder_deliver_more(self):
        logging.info('Start test_06_subcontracting_workorder_deliver_more.')
        if self.test_05:
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createOperations(self.test_bom, self.external_partner1)
            self.setupConsumedInOperation(self.test_bom_line1, self.op1)
            self.setupConsumedInOperation(self.test_bom_line2, self.op2)
            self.createSupplierInfo1()
            self.createProduction(3)
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            wo_raw_1 = self.env['mrp.workorder']
            wo_raw_2 = self.env['mrp.workorder']
            for wo in self.test_production.workorder_ids:
                if wo.operation_id == self.op1:
                    wo_raw_1 = wo
                elif wo.operation_id == self.op2:
                    wo_raw_2 = wo
            qty_delivered_extra = 100
            ext_wizard = self.execProduceExternallyWO(wo_raw_1)
            self.createTmpStockMove('Deliver %r X %r' % (self.raw_2.display_name, qty_delivered_extra), 
                                    self.raw_2, 
                                    qty_delivered_extra, 
                                    self.stock_location, 
                                    self.subcontract_loc_1, 
                                    self.external_partner1, 
                                    self.test_production.name, 
                                    self.test_production, 
                                    ext_wizard, 
                                    self.env["mrp.production.externally.wizard"],
                                    self.raw_2.uom_id,
                                    'mrp.workorder')
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'out')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 1000, 'out')
            ext_wizard = self.execProduceExternallyWO(wo_raw_2)
            ext_wizard.button_produce_externally()
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 100, 'out')
            out_pick_2, in_pick_2, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick_2 - out_pick)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 115, 'out')
            self.checkQuantQty(self.raw_2, self.stock_location, 885, 'out')
            self.validatePicking(in_pick_2 - in_pick)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 100, 'out')
            self.checkQuantQty(self.raw_2, self.stock_location, 900, 'out')
        
            purchase_ids = self.getPurchase(self.external_partner1, False, wo_raw_1)
            self.checkPurchase(purchase_ids, 6)
            purchase_ids = self.getPurchase(self.external_partner1, False, wo_raw_2)
            self.checkPurchase(purchase_ids, 15)
        logging.info('End test_06_subcontracting_workorder_deliver_more.')
        self.assertEqual(1, 1)
    
    def test_06_subcontracting_more_purchase_validate_only_one(self):
        logging.info('Start test_08_subcontracting_more_purchase_validate_only_one.')
        if self.test_06:
            self.createSubcontractLocation1()
            self.createSubcontractLocation2()
            self.createExternalPartner1()
            self.createExternalPartner2()
            self.createProducts()
            self.createBom()
            self.createSupplierInfo1()
            self.createSupplierInfo2()
            self.createProduction(3)
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, out_pick.picking_type_code)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, out_pick.picking_type_code)
            self.checkQuantQty(self.raw_1, self.stock_location, 994, out_pick.picking_type_code)
            self.checkQuantQty(self.raw_2, self.stock_location, 985, out_pick.picking_type_code)
            self.validatePicking(in_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, in_pick.picking_type_code)
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, in_pick.picking_type_code)
            self.checkQuantQty(self.raw_1, self.stock_location, 994, in_pick.picking_type_code)
            self.checkQuantQty(self.raw_2, self.stock_location, 985, in_pick.picking_type_code)
        
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner2)
            if out_pick.state != 'cancel':
                raise Exception('Second outgoing picking not cancelled.')
            if in_pick.state != 'cancel':
                raise Exception('Second incoming picking not cancelled.')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, 3)
            purchase_ids = self.getPurchase(self.external_partner2, self.test_production)
            if purchase_ids.state != 'cancel':
                raise Exception('Second purchase not cancelled.')
        logging.info('End test_08_subcontracting_more_purchase_validate_only_one.')
        self.assertEqual(1, 1)
    
    def test_07_subcontracting_MO_backorders(self):
        logging.info('Start test_09_subcontracting_MO_backorders.')
        if self.test_07:
            finished_to_produce = 3
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            self.validatePicking(in_pick, 1)
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.finished, self.stock_location, 1, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 4, 'in')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'in')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 10, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', in_pick.id)])
            self.validatePicking(backorder_pick, 2)
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.finished, self.stock_location, 3, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'in')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, finished_to_produce)
        logging.info('End test_09_subcontracting_MO_backorders.')
        self.assertEqual(1, 1)
    
    def test_08_subcontracting_MO_cancel(self):
        logging.info('Start test_10_subcontracting_MO_cancel.')
        if self.test_08:
            finished_to_produce = 3
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, _dropship_pick, _internal_pick = self.getExtPickings(self.test_production, self.external_partner1)
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            self.cancelMo(self.test_production)
            for pick in out_pick:
                if pick.state != 'done':
                    pick.action_cancel()
            for pick in in_pick:
                pick.action_cancel()
                if pick.state != 'cancel':
                    raise Exception('Picking in %r not cancelled.' % (pick.display_name))
            #self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
            #self.checkQuantQty(self.finished, self.stock_location, 0, 'in')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 6, 'out')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
            self.checkQuantQty(self.raw_1, self.stock_location, 994, 'in')
            self.checkQuantQty(self.raw_2, self.stock_location, 985, 'in')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            for purchase in purchase_ids:
                if purchase.state != 'cancel':
                    raise Exception('Cancel purchase wrong')
        logging.info('End test_10_subcontracting_MO_cancel.')
        self.assertEqual(1, 1)
    
    def test_09_subcontracting_cancel_produce_externally_and_resume_production(self):
        logging.info('Start test_11_subcontracting_cancel_produce_externally_and_resume_production.')
        if self.test_09:
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createOperations(self.test_bom, self.external_partner1)
            self.setupConsumedInOperation(self.test_bom_line1, self.op1)
            self.setupConsumedInOperation(self.test_bom_line2, self.op2)
            self.createSupplierInfo1()
            self.createProduction(3)
            wo_raw_1, wo_raw_2 = self.getWorkorders(self.test_production, self.op1, self.op2)
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.button_produce_externally()
            self.cancelMo(self.test_production)
        
            self.test_production.action_confirm()
            wo_raw_1.button_start()
            wo_raw_1.button_finish()
            wo_raw_2.button_start()
            wo_raw_2.button_finish()
            self.test_production.action_assign()
            for raw in self.test_production.move_raw_ids:
                if raw.state == 'assigned':
                    for raw_line in raw.move_line_ids:
                        raw_line.qty_done = raw_line.product_uom_qty
            self.test_production.button_mark_done()
            if self.test_production.state != 'done':
                raise Exception('Cancel production externally MO and go back with normal flow not working')
        logging.info('End test_11_subcontracting_cancel_produce_externally_and_resume_production.')
        self.assertEqual(1, 1)
    
    def test_10_subcontracting_cancel_produce_externally_wo_and_resume_production(self):
        logging.info('Start test_12_subcontracting_cancel_produce_externally_wo_and_resume_production.')
        if self.test_10:
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createProducts()
            self.createBom()
            self.createOperations(self.test_bom, self.external_partner1)
            self.setupConsumedInOperation(self.test_bom_line1, self.op1)
            self.setupConsumedInOperation(self.test_bom_line2, self.op2)
            self.createSupplierInfo1()
            self.createProduction(3)
            wo_raw_1, wo_raw_2 = self.getWorkorders(self.test_production, self.op1, self.op2)
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyWO(wo_raw_1)
            ext_wizard.button_produce_externally()
            self.cancelWo(wo_raw_1)
            self.test_production.action_confirm()
            wo_raw_1.button_start()
            wo_raw_1.button_finish()
            wo_raw_2.button_start()
            wo_raw_2.button_finish()
            self.test_production.action_assign()
            for raw in self.test_production.move_raw_ids:
                if raw.state == 'assigned':
                    for raw_line in raw.move_line_ids:
                        raw_line.qty_done = raw_line.product_uom_qty
            self.test_production.button_mark_done()
            if self.test_production.state != 'done':
                raise Exception('Cancel production externally MO and go back with normal flow not working')
        logging.info('End test_12_subcontracting_cancel_produce_externally_wo_and_resume_production.')
        self.assertEqual(1, 1)

    def test_11_subcontracting_dropship(self):
        logging.info('Start test_11_subcontracting_dropship.')
        if self.test_11:
            finished_to_produce = 1
            self.createSubcontractLocation1()
            self.createExternalPartner1()
            self.createSubcontractLocation2()
            self.createExternalPartner2()
            self.createSubcontractLocation3()
            self.createExternalPartner3()
            self.createProducts()
            self.createBom()
            self.createProduction(finished_to_produce)
            self.createSupplierInfo1()
            self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
            self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
            ext_wizard = self.execProduceExternallyMO(self.test_production)
            ext_wizard.is_dropship = True
            ext_wizard.external_partner = [(0, 0, {
                'partner_id': self.external_partner2.id,
                'price': 20,
                'sequence': 20, # default 10
                })]
            ext_wizard.external_partner = [(0, 0, {
                'partner_id': self.external_partner3.id,
                'price': 30,
                'sequence': 5, # default 10
                })]
            ext_wizard.changeExternalPartner()
            ext_wizard.button_produce_externally()
            out_pick, in_pick, _manuf_pick, dropship_pick, _internal_pick = self.getExtPickings(self.test_production)
            if len(dropship_pick) != 2:
                raise Exception('Wrong Dropships')
            if len(out_pick) != 1:
                raise Exception('Wrong Out Picks')
            if len(in_pick) != 1:
                raise Exception('Wrong In Picks')
            self.validatePicking(out_pick)
            self.checkQuantQty(self.raw_1, self.subcontract_loc_3, 2, '')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_3, 5, '')
            self.validatePicking(out_pick.dropship_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_3, -1, '')
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 1, '')
            self.validatePicking(out_pick.dropship_pick.dropship_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_3, -1, '')
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, '')
            self.checkQuantQty(self.finished, self.subcontract_loc_2, 1, '')
            self.validatePicking(in_pick)
            self.checkQuantQty(self.finished, self.subcontract_loc_3, 0, '')
            self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, '')
            self.checkQuantQty(self.finished, self.subcontract_loc_2, 0, '')
            self.checkQuantQty(self.raw_1, self.subcontract_loc_3, 0, '')
            self.checkQuantQty(self.raw_2, self.subcontract_loc_3, 0, '')
            self.checkQuantQty(self.raw_1, self.stock_location, 998, '')
            self.checkQuantQty(self.raw_2, self.stock_location, 995, '')
            self.checkQuantQty(self.finished, self.stock_location, 1, '')
            purchase_ids = self.getPurchase(self.external_partner1, self.test_production)
            self.checkPurchase(purchase_ids, finished_to_produce)
            purchase_ids = self.getPurchase(self.external_partner2, self.test_production)
            self.checkPurchase(purchase_ids, finished_to_produce)
            purchase_ids = self.getPurchase(self.external_partner3, self.test_production)
            self.checkPurchase(purchase_ids, finished_to_produce)
        logging.info('End test_11_subcontracting_dropship.')
        self.assertEqual(1, 1)
