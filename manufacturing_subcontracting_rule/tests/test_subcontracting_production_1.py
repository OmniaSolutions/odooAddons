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
        super(TestSubcontracting, self).setUp()

    def createProduction(self, finish_qty=1):
        production_env = self.env['mrp.production']
        production_form = Form(production_env)
        production_form.product_id = self.finished
        production_form.bom_id = self.test_bom
        production_form.product_qty = finish_qty
        self.test_production = production_form.save()
        self.stock_location = self.test_production.location_src_id

    def createSubcontractLocation(self):
        location_env = self.env['stock.location']
        self.subcontract_loc_1 = location_env.create({
            'name': 'Test Subcontract Loc 1',
            'usage': 'customer',
            })

    def createExternalPartner(self):
        partner_env = self.env['res.partner']
        external_partner_form = Form(partner_env)
        try:
            external_partner_form.name = 'Test Supplier 1'
        except:
            external_partner_form.firstname = 'Test'
            external_partner_form.lastname = 'Supplier 1'
        external_partner_form.location_id = self.subcontract_loc_1
        self.external_partner = external_partner_form.save()

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

    def createSupplierInfo(self):
        supplierinfo = self.env['product.supplierinfo']
        self.finished_supplierinfo_1 = supplierinfo.create({
            'name': self.external_partner.id,
            'product_tmpl_id': self.finished_service.product_tmpl_id.id,
            'product_id': self.finished_service.id,
            })

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

    def execProduceExternally(self, production):
        vals = production.button_produce_externally()
        model = vals.get('res_model', '')
        res_id = vals.get('res_id', False)
        ext_wizard = self.env[model].browse(res_id)
        ext_wizard = ext_wizard.with_context({
            'active_model': production._name,
            'active_ids': production.id,
            })
        return ext_wizard

    def getExtPickings(self, production):
        pick_model = self.env['stock.picking']
        ext_picks = production.getExtPickIds()
        if not ext_picks:
            raise Exception('No pickings created')
        elif len(ext_picks) != 2:
            raise Exception('Wrong number of pickings created')
        out_pick = self.env['stock.picking']
        in_pick = self.env['stock.picking']
        for pick in pick_model.browse(ext_picks):
            if pick.picking_type_code == 'outgoing':
                out_pick = pick
            elif pick.picking_type_code == 'incoming':
                in_pick = pick
        if not out_pick:
            raise Exception('Out picking not created')
        if not in_pick:
            raise Exception('In picking not created')
        return out_pick, in_pick

    def validatePicking(self, pick):
        pick.action_confirm()
        pick.action_assign()
        res = pick.button_validate()
        if isinstance(res, dict) and res['res_model'] == 'stock.immediate.transfer':
            immediate_transfer_form = Form(self.env[res['res_model']].with_context(res['context']))
            immediate_transfer = immediate_transfer_form.save()
            immediate_transfer.process()

    def createTmpStockMove(self, name, product_id, qty, location_id, location_dest_id, partner_id, origin, production_id, external_prod_raw, external_prod_finish, product_uom, operation_type):
        tmp_move_env = self.env["stock.tmp_move"]
        vals = {
            'name': name,
            'product_id': product_id.id,
            'product_uom_qty': qty,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': partner_id.id,
            'origin': origin,
            'production_id': production_id.id,
            'external_prod_raw': external_prod_raw.id,
            'external_prod_finish': external_prod_finish.id,
            'product_uom': product_uom.id,
            'operation_type': operation_type,
            }
        return tmp_move_env.create(vals)

    #
    # def test_01_subcontracting_simple_1(self):
    #     logging.info('Check Standard manufacturing external production start.')
    #     self.createSubcontractLocation()
    #     self.createExternalPartner()
    #     self.createProducts()
    #     self.createBom()
    #     self.createProduction()
    #     self.createSupplierInfo()
    #     self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
    #     self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
    #     ext_wizard = self.execProduceExternally(self.test_production)
    #     ext_wizard.button_produce_externally()
    #     out_pick, in_pick = self.getExtPickings(self.test_production)
    #     self.validatePicking(out_pick)
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 2, 'out')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 5, 'out')
    #     self.validatePicking(in_pick)
    #     self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.finished, self.stock_location, 1, 'in')
    #     logging.info('Check Standard manufacturing external production successfully.')
    #     self.assertEqual(1, 1)
    
    # def test_02_subcontracting_send_more(self):
    #     logging.info('Check Deliver extra manufacturing external production start.')
    #     self.createSubcontractLocation()
    #     self.createExternalPartner()
    #     self.createProducts()
    #     self.createBom()
    #     self.createProduction()
    #     self.createSupplierInfo()
    #     self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
    #     self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
    #     #self.updateStartingStockQty(self.finished, self.subcontract_loc_1, 5)
    #     ext_wizard = self.execProduceExternally(self.test_production)
    #     qty_delivered_extra = 10
    #     self.createTmpStockMove('Deliver %r X %r' % (self.raw_2.display_name, qty_delivered_extra), 
    #                             self.raw_2, 
    #                             qty_delivered_extra, 
    #                             self.stock_location, 
    #                             self.subcontract_loc_1, 
    #                             self.external_partner, 
    #                             self.test_production.name, 
    #                             self.test_production, 
    #                             ext_wizard, 
    #                             self.env["mrp.production.externally.wizard"],
    #                             self.raw_2.uom_id, 
    #                             'deliver')
    #     self.createTmpStockMove('Get %r X %r' % (self.finished.display_name, qty_delivered_extra), 
    #                             self.finished, 
    #                             5, 
    #                             self.subcontract_loc_1, 
    #                             self.stock_location, 
    #                             self.external_partner, 
    #                             self.test_production.name, 
    #                             self.test_production, 
    #                             self.env["mrp.production.externally.wizard"],
    #                             ext_wizard, 
    #                             self.finished.uom_id, 
    #                             'deliver_consume')
    #     ext_wizard.button_produce_externally()
    #     out_pick, in_pick = self.getExtPickings(self.test_production)
    #     self.validatePicking(out_pick)
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 2, 'out')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 15, 'out')
    #     self.validatePicking(in_pick)
    #     self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, -10, 'in')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, -15, 'in')
    #     self.checkQuantQty(self.finished, self.stock_location, 6, 'in')
    #     logging.info('Check Deliver extra manufacturing external production successfully.')
    #     self.assertEqual(1, 1)
    
    # def test_03_subcontracting_consume_more(self):
    #     logging.info('Check Consume extra manufacturing external production start.')
    #     self.createSubcontractLocation()
    #     self.createExternalPartner()
    #     self.createProducts()
    #     self.createBom()
    #     self.createProduction()
    #     self.createSupplierInfo()
    #     qty_delivered_extra = 100
    #     self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
    #     self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
    #     self.updateStartingStockQty(self.raw_2, self.subcontract_loc_1, qty_delivered_extra)
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 100, 'out')
    #     ext_wizard = self.execProduceExternally(self.test_production)
    #     self.createTmpStockMove('Deliver %r X %r' % (self.raw_2.display_name, qty_delivered_extra), 
    #                             self.raw_2, 
    #                             qty_delivered_extra, 
    #                             self.stock_location, 
    #                             self.subcontract_loc_1, 
    #                             self.external_partner, 
    #                             self.test_production.name, 
    #                             self.test_production, 
    #                             ext_wizard, 
    #                             self.env["mrp.production.externally.wizard"],
    #                             self.raw_2.uom_id, 
    #                             'consume')
    #     ext_wizard.button_produce_externally()
    #     out_pick, in_pick = self.getExtPickings(self.test_production)
    #     self.validatePicking(out_pick)
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 2, 'out')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 5, 'out')
    #     self.validatePicking(in_pick)
    #     self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.finished, self.stock_location, 1, 'in')
    #     logging.info('Check Consume extra manufacturing external production successfully.')
    #     self.assertEqual(1, 1)
    #
    # def test_04_subcontracting_receive_less(self):
    #     logging.info('Check Consume extra manufacturing external production start.')
    #     self.createSubcontractLocation()
    #     self.createExternalPartner()
    #     self.createProducts()
    #     self.createBom()
    #     self.createProduction(3)
    #     self.createSupplierInfo()
    #     self.updateStartingStockQty(self.raw_1, self.stock_location, 1000)
    #     self.updateStartingStockQty(self.raw_2, self.stock_location, 1000)
    #     ext_wizard = self.execProduceExternally(self.test_production)
    #     for move in ext_wizard.move_finished_ids:
    #         move.product_uom_qty = 2 # 3
    #     for move in ext_wizard.move_raw_ids:
    #         if move.product_id == self.raw_1:
    #             move.product_uom_qty = 1 # 2
    #         if move.product_id == self.raw_2:
    #             move.product_uom_qty = 3 # 5
    #     ext_wizard.button_produce_externally()
    #     out_pick, in_pick = self.getExtPickings(self.test_production)
    #     self.validatePicking(out_pick)
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, 1, 'out')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, 3, 'out')
    #     self.validatePicking(in_pick)
    #     self.checkQuantQty(self.finished, self.subcontract_loc_1, 0, 'in')
    #     self.checkQuantQty(self.raw_1, self.subcontract_loc_1, -3, 'in')
    #     self.checkQuantQty(self.raw_2, self.subcontract_loc_1, -7, 'in')
    #     self.checkQuantQty(self.finished, self.stock_location, 2, 'in')
    #     logging.info('Check Consume extra manufacturing external production successfully.')
    #     self.assertEqual(1, 1)


