'''
Created on Sep 17, 2018

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
import logging
from datetime import datetime


class MrpProductionWCLine(models.Model):
    _inherit = 'mrp.workorder'
    
    user_ids = fields.Many2many('res.users', string='Users')
    
    def getDictWorkorder(self, woBrwsList):
        out = []
        for woBrws in woBrwsList:
            if woBrws.production_id.state in ['confirm', 'planned', 'progress']:
                woDict = {
                    'wo_id': woBrws.id,
                    'wo_name': woBrws.name,
                    'wo_description': '',
                    'production_name': woBrws.production_id.name,
                    'product_name': woBrws.product_id.name,
                    'product_default_code': woBrws.product_id.default_code or '',
                    'wo_state': woBrws.state,
                    'qty': "%s / %s %s" %(woBrws.qty_produced, woBrws.qty_production, woBrws.product_uom_id.name),
                    'date_planned': woBrws.date_planned_start or '',
                    'is_user_working': woBrws.is_user_working,
                    }
                out.append(woDict)
        return out
    
    @api.model
    def getWorkorders(self, workcenter, workorder=False, listify=False):
        logging.info('Getting Work Orders with parameters %r, workorder %r' % (workcenter, workorder))
        searchFilter = [('state', 'in', ['ready', 'progress']),
                        ('workcenter_id', '=', workcenter)
                        ]
        if workorder:
            searchFilter.append(('id', '=', workorder))
        logging.info('Getting Work Orders with search %r' % (searchFilter))
        woBrwsList = self.search(searchFilter, order='date_planned_start ASC,id ASC')
        out = self.getDictWorkorder(woBrwsList)
        if listify:
            out = self.listifyForInterface(out)
        return out

    @api.model
    def getWorkordersByUser(self, user_id, listify=False):
        user_id = int(user_id)
        if user_id == 0:
            return []
        searchFilter = [('state', 'in', ['ready', 'progress'])]
        logging.info('Getting Work Orders with search %r' % (searchFilter))
        woBrwsList = self.search(searchFilter, order='date_planned_start ASC,id ASC')
        woBrwsList = woBrwsList.filtered(lambda x: user_id in x.user_ids.ids or x.user_id.id == user_id)
        out = self.getDictWorkorder(woBrwsList)
        if listify:
            out = self.listifyForInterface(out)
        return out

    def listifyForInterface(self, woList):
        lines = []
        for dictRes in woList:
            lines.append(
                [
                    dictRes.get('wo_id', ''),
                    dictRes.get('product_name', ''),
                    dictRes.get('product_default_code', ''),
                    dictRes.get('wo_name', ''),
                    dictRes.get('production_name', ''),
                    dictRes.get('wo_description', ''),
                    dictRes.get('wo_state', ''),
                    dictRes.get('qty', 0),
                    dictRes.get('date_planned', ''),
                    str(dictRes.get('is_user_working', False)),
                    str(r"/web/mrp/get_worksheet/" + str(dictRes.get('wo_id', '')))
                ])
        return lines

    def listify(self, val):
        if isinstance(val, (list, tuple)):
            return val
        elif isinstance(val, (int, float)):
            return [val]
        return []

    @api.model
    def startWork(self, workorder):
        if not workorder:
            return False
        woLine = self.browse(self.listify(workorder))
        for woBrws in woLine:
            return woBrws.button_start()
        return False

    @api.model
    def pauseWork(self, workorder):
        if not workorder:
            return False
        woLine = self.browse(self.listify(workorder))
        for woBrws in woLine:
            return woBrws.button_pending()
        return False
    
    @api.model
    def resumeWork(self, workorder):
        if not workorder:
            return False
        woLine = self.browse(self.listify(workorder))
        for woBrws in woLine:
            return woBrws.button_start()
        return False
    
    @api.model
    def recordWork(self, workorder, n_pieces=0, n_scrap=0.0):
        if not workorder:
            return False
        work_order_ids = self.browse(self.listify(workorder))
        work_order_ids._recordWork(n_pieces,
                                   n_scrap)
        
    def _recordWork(self,
                    n_pieces=0,
                    n_scrap=0.0):
        for work_order_id in self:
            if n_pieces > 0:
                work_order_id.qty_producing = n_pieces
                work_order_id.record_production()
            if n_scrap > 0:
                work_order_id.o_do_scrap(n_scrap)
        return False

    @api.model
    def o_do_scrap(self, scrap_qty):
        stock_scrap = self.env['stock.scrap']
        product_product = self.env['product.product']
        for product_id in (self.production_id.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel')) | self.production_id.move_finished_ids.filtered(lambda x: x.state == 'done')).mapped('product_id').ids:
            product_id = product_product.browse(product_id)
            val = {'workorder_id': self.id,
                   'production_id': self.production_id.id,
                   'product_id':  product_id.id,
                   'product_uom_id': product_id.uom_id.id,
                   'scrap_qty': scrap_qty
                   }
            stock_scrap_id = stock_scrap.create(val)
            stock_scrap_id.do_scrap()
#
# workorder simple
#
    
    @api.model
    def getWorkorder(self,
                     workcenter_id,
                     status=[]):
        out = {}
        out['thead'] = [['Wo.Id', 'MO.Name','Product', 'Qty.P', 'Qty']]
        body_row = []
        for workorder_id in self.env['mrp.workorder'].search([('workcenter_id','=', workcenter_id.id),
                                                              ('state', 'in', status)]):
            body_row.append([workorder_id.id,
                             workorder_id.display_name,
                             workorder_id.product_id.display_name,
                             workorder_id.qty_produced,
                             workorder_id.qty_production])
        
        out['tbody'] = body_row
        return out

    @api.model
    def getReadyWorkorder(self,
                          workcenter_id):
        out = self.getWorkorder(workcenter_id, ['ready'])
        out['table_name']='ready_workorder_table'
        return out

    @api.model
    def getInProgressWorkorder(self,
                               workcenter_id):
        out = self.getWorkorder(workcenter_id, ['progress'])
        out['table_name']='active_workorder_table'
        return out
    
    @api.model
    def confirm_start_workorder(self, workorder_id):
        for mrp_workorder_id in self.browse([int(workorder_id)]):
            if mrp_workorder_id.state in ['progress']:
                mrp_workorder_id._recordWork(mrp_workorder_id.qty_production - mrp_workorder_id.qty_produced)
            if mrp_workorder_id.state in ['ready']:
                mrp_workorder_id.button_start()
