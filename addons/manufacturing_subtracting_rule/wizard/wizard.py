'''
Created on 16 Jan 2018

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class MrpProductionWizard(models.Model):

    _name = "mrp.production.externally.wizard"

    external_partner = fields.Many2one('res.partner', string='External Partner', required=True)

    move_raw_ids = fields.One2many('stock.move',
                                    string='Raw Materials',
                                    inverse_name='external_prod_raw',
                                    domain=[('scrapped', '=', False)])

    move_finished_ids = fields.One2many('stock.move',
                                         string='Finished Products',
                                         inverse_name='external_prod_finish',
                                         domain=[('scrapped', '=', False)])

    @api.multi
    def button_produce_externally(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        productionBrws = relObj.browse(objIds)
        productionBrws.write({'external_partner': self.external_partner.id,
                              'state': 'external'})
        self.createStockPickingIn(self.external_partner, productionBrws)
        self.createStockPickingOut(self.external_partner, productionBrws)
        productionBrws.button_unreserve()   # Needed to evaluate picking out move

    def getOrigin(self, productionBrws, originBrw=None):
        return productionBrws.name

    def getLocation(self, originBrw):
        if originBrw:
            return originBrw.operation_id.routing_id.location_id.id
        for lock in self.env['stock.location'].search([('usage', '=', 'supplier'),
                                                       ('active', '=', True),
                                                       ('company_id', '=', False)]):
            return lock.id
        return False

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
        loc = self.getLocation(originBrw)
        toCreate = {'partner_id': partner.id,
                    'location_id': loc,
                    'location_src_id': loc,
                    'location_dest_id': productionBrws.location_src_id.id,
                    'min_date': productionBrws.date_planned_start,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': []}
        for productionLineBrws in productionBrws.move_finished_ids:
            toCreate['move_lines'].append(
                (0, False, {
                    'product_id': productionLineBrws.product_id.id,
                    'product_uom_qty': productionLineBrws.product_uom_qty,
                    'product_uom': productionLineBrws.product_uom.id,
                    'name': productionLineBrws.name,
                    'state': 'assigned'}))
        stockObj.create(toCreate)

    def createStockPickingOut(self, partner, productionBrws, originBrw=None):
        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'outgoing'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        stockObj = self.env['stock.picking']
        toCreate = {'partner_id': partner.id,
                    'location_id': productionBrws.location_src_id.id,
                    'location_dest_id': self.getLocation(originBrw),
                    'location_src_id': productionBrws.location_src_id.id,
                    'min_date': datetime.datetime.now(),
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': self.getOrigin(productionBrws, originBrw),
                    'move_lines': []}
        for productionLineBrws in productionBrws.move_raw_ids:
            toCreate['move_lines'].append(
                (0, False, {
                    'product_id': productionLineBrws.product_id.id,
                    'product_uom_qty': productionLineBrws.product_uom_qty,
                    'product_uom': productionLineBrws.product_uom.id,
                    'name': productionLineBrws.name,
                    'state': 'assigned'}))
        stockObj.create(toCreate)

#  operation_id e' l'operazione del ruting che vado a fare mi da 'oggetto


class MrpWorkorderWizard(MrpProductionWizard):

    _name = "mrp.workorder.externally.wizard"
    external_partner = fields.Many2one('res.partner', string='External Partner', required=True)

    operation_type = fields.Selection(selection=[('normal', _('Normal')), ('consume', _('Consume'))],
                                      string=_('Operation'))
    
    consume_product_id = fields.Many2one(comodel_name='product.product', string=_('Product To Consume'))
    consume_bom_id = fields.Many2one(comodel_name='mrp.bom', string=_('BOM To Consume'))

    @api.multi
    def button_produce_externally(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        workorderBrws = relObj.browse(objIds)
        workorderBrws.write({'external_partner': self.external_partner.id,
                             'state': 'external'})
        productionBrws = workorderBrws.production_id
        self.createStockPickingIn(self.external_partner, productionBrws, workorderBrws)
        self.createStockPickingOut(self.external_partner, productionBrws, workorderBrws)
        productionBrws.button_unreserve()   # Needed to evaluate picking out move

    def getOrigin(self, productionBrws, originBrw):
        return "%s - %s - %s" % (productionBrws.name, originBrw.name, originBrw.external_partner.name)
