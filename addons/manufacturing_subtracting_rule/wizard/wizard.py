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

# delete from stock_quant;
# delete from stock_move;
# delete from stock_picking;
# delete from mrp_workorder;
# delete from mrp_production;
# 
# select * from stock_quant
# select * from stock_move
# select * from stock_picking
# select * from stock_picking_type
# select * from stock_immediate_transfer

class MrpProductionWizard(models.Model):

    _name = "mrp.production.externally.wizard"

    external_partner = fields.Many2one('res.partner', string='External Partner', required=True)

    move_raw_ids = fields.One2many('stock.tmp_move',
                                    string='Raw Materials',
                                    inverse_name='external_prod_raw',
                                    domain=[('scrapped', '=', False)])

    move_finished_ids = fields.One2many('stock.tmp_move',
                                         string='Finished Products',
                                         inverse_name='external_prod_finish',
                                         domain=[('scrapped', '=', False)])

    operation_type = fields.Selection(selection=[('normal', _('Normal')), ('consume', _('Consume'))],
                                      string=_('Operation'),
                                      default='normal')
    
    consume_product_id = fields.Many2one(comodel_name='product.product', string=_('Product To Consume'))
    consume_bom_id = fields.Many2one(comodel_name='mrp.bom', string=_('BOM To Consume'))

    external_warehouse_id = fields.Many2one('stock.warehouse', string='External Warehouse')
    external_location_id = fields.Many2one('stock.location', string='External Location')
    production_id = fields.Many2one('mrp.production', string='Production', readonly=True)

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
        for lineBrws in prodObj.move_raw_ids:
            lineBrws.action_cancel()
        for lineBrws in prodObj.move_finished_ids:
            lineBrws.action_cancel()

    def updateMoveLines(self, productionBrws):
        move_raw_ids = []
        move_finished_ids = []
        productsToCheck = []
        for lineBrws in self.move_raw_ids:
            productsToCheck.append(lineBrws.product_id.id)
            vals = {
                'name': lineBrws.name,
                'company_id': lineBrws.company_id.id,
                'product_id': lineBrws.product_id.id,
                'product_uom_qty': lineBrws.product_uom_qty,
                'location_id': lineBrws.location_id.id,
                'location_dest_id': lineBrws.location_dest_id.id,
                'partner_id': self.external_partner.id,
                'note': lineBrws.note,
                'state': 'confirmed',
                'origin': lineBrws.origin,
                'warehouse_id': lineBrws.warehouse_id.id,
                'production_id': False,
                'product_uom': lineBrws.product_uom.id,
            }
            move_raw_ids.append((0, False, vals))
        for lineBrws in self.move_finished_ids:
            productsToCheck.append(lineBrws.product_id.id)
            vals = {
                'name': lineBrws.name,
                'company_id': lineBrws.company_id.id,
                'product_id': lineBrws.product_id.id,
                'product_uom_qty': lineBrws.product_uom_qty,
                'location_id': lineBrws.location_id.id,
                'location_dest_id': lineBrws.location_dest_id.id,
                'partner_id': self.external_partner.id,
                'note': lineBrws.note,
                'state': 'confirmed',
                'origin': lineBrws.origin,
                'warehouse_id': lineBrws.warehouse_id.id,
                'production_id': productionBrws.id,
                'product_uom': lineBrws.product_uom.id,
            }
            move_finished_ids.append((0, False, vals))
        productionBrws.write({
            'move_raw_ids': move_raw_ids,
            'move_finished_ids': move_finished_ids,
            'state': 'external',
            'external_partner': self.external_partner.id
            })
        productsToCheck = list(set(productsToCheck))
        for product in self.env['product.product'].browse(productsToCheck):
            productionBrws.checkCreateReorderRule(product, productionBrws.location_src_id.get_warehouse())
        
    @api.multi
    def button_produce_externally(self):
        productionBrws = self.getParentProduction()
        self.cancelProductionRows(productionBrws)
        self.updateMoveLines(productionBrws)
        self.createStockPickingIn(self.external_partner, productionBrws)
        self.createStockPickingOut(self.external_partner, productionBrws)
        #productionBrws.button_unreserve()   # Needed to evaluate picking out move
#         productionBrws.move_raw_ids.action_done()


#         productionBrws.move_raw_ids.write({'state': 'done'})
#         productionBrws.move_finished_ids.write({'state': 'done'})

    @api.multi
    def button_close_wizard(self):
        self.move_raw_ids.unlink()
        self.move_finished_ids.unlink()
        self.unlink()
        
    def getOrigin(self, productionBrws, originBrw=None):
        return productionBrws.name

#     def getLocation(self, originBrw):
#         if originBrw:
#             return originBrw.operation_id.routing_id.location_id.id
#         for lock in self.env['stock.location'].search([('usage', '=', 'supplier'),
#                                                        ('active', '=', True),
#                                                        ('company_id', '=', False)]):
#             return lock.id
#         return False

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
        localStockLocation = productionBrws.location_src_id # Taken from manufacturing order
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
                    'state': 'draft'}
        obj = stockObj.create(toCreate)
        #obj.write({'move_lines': [(6, False, incomingMoves)]})
        
        newStockLines = []
        for outMove in incomingMoves:
            stockMove = outMove.copy(default={
                'production_id': False,
                'raw_material_production_id': False
                })
            newStockLines.append(stockMove.id)
        obj.write({'move_lines': [(6, False, newStockLines)]})

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
        localStockLocation = productionBrws.location_src_id # Taken from manufacturing order
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
                    'state': 'draft'}
        obj = stockObj.create(toCreate)
        
        newStockLines = []
        for outMove in outGoingMoves:
            stockMove = outMove.copy(default={
                'production_id': False,
                'raw_material_production_id': False
                })
            newStockLines.append(stockMove.id)
        obj.write({'move_lines': [(6, False, newStockLines)]})

    @api.multi
    def write(self, vals):
        return super(MrpProductionWizard, self).write(vals)
#  operation_id e' l'operazione del ruting che vado a fare mi da 'oggetto


class MrpWorkorderWizard(MrpProductionWizard):

    _name = "mrp.workorder.externally.wizard"
    _inherit = ['mrp.production.externally.wizard']
    
    #external_partner = fields.Many2one('res.partner', string='External Partner', required=True)

#     operation_type = fields.Selection(selection=[('normal', _('Normal')), ('consume', _('Consume'))],
#                                       string=_('Operation'))
#     
#     consume_product_id = fields.Many2one(comodel_name='product.product', string=_('Product To Consume'))
#     consume_bom_id = fields.Many2one(comodel_name='mrp.bom', string=_('BOM To Consume'))

    move_raw_ids = fields.One2many('stock.move',
                                    string='Raw Materials',
                                    inverse_name='external_prod_workorder_raw',
                                    domain=[('scrapped', '=', False)])

    move_finished_ids = fields.One2many('stock.move',
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
        self.createStockPickingIn(self.external_partner, productionBrws, workorderBrws)
        self.createStockPickingOut(self.external_partner, productionBrws, workorderBrws)
        productionBrws.button_unreserve()   # Needed to evaluate picking out move

    def getOrigin(self, productionBrws, originBrw):
        return "%s - %s - %s" % (productionBrws.name, originBrw.name, originBrw.external_partner.name)
