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


class MrpWorkorderWizard(models.TransientModel):
    _name = "mrp.workorder.externally.wizard"
    _inherit = ['mrp.production.externally.wizard']
    _description='Sub-Contracting Mrp Production Externally wizard'
    
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

    def getPickingVals(self, partner_id, mrp_production_id, operation_type):
        ret = super(MrpWorkorderWizard, self).getPickingVals(partner_id, mrp_production_id, operation_type)
        ret['sub_workorder_id'] = self.getWo().id
        return ret

    def getOrigin(self, productionBrws):
        mrp_workorder_id = self.getWo()
        return "%s - %s - %s" % (productionBrws.name, mrp_workorder_id.name, mrp_workorder_id.external_partner.name)

    def getStockMoveVals(self, stock_move_id, mrp_production_id, out_stock_picking_id, location_id, location_dest_id):
        ret = super(MrpWorkorderWizard, self).getStockMoveVals(stock_move_id, mrp_production_id, out_stock_picking_id, location_id, location_dest_id)
        ret['mrp_workorder_id'] = self.getWo().id
        ret['workorder_id'] = self.getWo().id
        return ret

    def getPurchaseVals(self, external_partner):
        ret = super(MrpWorkorderWizard, self).getPurchaseVals(external_partner)
        ret['workorder_external_id'] = self.getWo().id
        return ret

    def getPurchaseLineVals(self, product, purchase, move_line):
        ret = super(MrpWorkorderWizard, self).getPurchaseLineVals(product, purchase, move_line)
        ret['workorder_external_id'] = self.getWo().id
        return ret

    def getDefaultProductionServiceProduct(self):
        mrp_workorder_id = self.getWo()
        if mrp_workorder_id.external_product:
            return mrp_workorder_id.external_product
        product_vals = self.getNewExternalProductInfo()
        newProduct = self.env['product.product'].search([('default_code', '=', product_vals.get('default_code'))])
        if not newProduct:
            newProduct = self.env['product.product'].create(product_vals)
            newProduct.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Create automatically from subcontracting module</b></div>'),
                                    message_type='notification')
            newProduct.type = 'service'
        mrp_workorder_id.external_product = newProduct
        mrp_workorder_id.operation_id.external_product = newProduct
        return newProduct
    
    @api.model
    def getNewExternalProductInfo(self):
        ret = super(MrpWorkorderWizard, self).getNewExternalProductInfo()
        workorder_id = self.getWo()
        ret['default_code'] = ret['default_code'] + "-" + workorder_id.name
        ret['name'] = ret['name'] + "-" + workorder_id.name
        return ret

    def getWo(self):
        out = self.env['mrp.workorder']
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        if model == 'mrp.workorder':
            out = relObj.browse(objIds)
        return out
        
    def button_produce_externally(self):
        if not self.external_partner:
            raise UserError(_("No partner selected"))
        pickingBrwsList = []
        mrp_workorder_id = self.getWo()
        mrp_workorder_id.write({'external_partner': self.external_partner.partner_id.id,
                                'state': 'external'})
        mrp_production_id = mrp_workorder_id.production_id
        for external_partner in self.external_partner:
            pickOut = self.createStockPickingOut(external_partner.partner_id, mrp_production_id, False)
            pickIn = self.createStockPickingIn(external_partner.partner_id, mrp_production_id, False)
            pickingBrwsList.extend((pickIn.id, pickOut.id))
            date_planned_finished = pickIn.scheduled_date
            date_planned_start = pickOut.scheduled_date
            _po_created = self.createPurchase(external_partner, pickIn)
        mrp_workorder_id.state = 'pending'
        mrp_workorder_id.date_planned_finished = date_planned_finished
        mrp_workorder_id.date_planned_start = date_planned_start
        mrp_production_id.external_pickings = [(6, 0, pickingBrwsList)]
        mrp_workorder_id.state = 'external'


    def create_vendors_from(self, partner_id):
        external_production_partner = self.env['external.workorder.partner']
        vals = {'partner_id': partner_id.id,
                'price': 0.0,
                'delay': 0.0,
                'min_qty': 0.0,
                'wizard_id': self.id
                }
        ret = external_production_partner.create(vals)
        self.changeExternalPartner('external.workorder.partner')
        return ret



