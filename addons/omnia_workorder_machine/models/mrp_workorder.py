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

    @api.model
    def getWorkorders(self, workcenter, workorder=False):
        out = []
        logging.info('Getting Work Orders with parameters %r, workorder %r' % (workcenter, workorder))
        searchFilter = [('state', 'in', ['pending', 'ready', 'progress']),
                        ('workcenter_id', '=', workcenter)
                        ]
        if workorder:
            searchFilter.append(('id', '=', workorder))
        logging.info('Getting Work Orders with search %r' % (searchFilter))
        woBrwsList = self.search(searchFilter, order='date_planned_start ASC,id ASC')
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
                    'qty': woBrws.qty_production,
                    'date_planned': woBrws.date_planned_start or '',
                    'is_user_working': woBrws.is_user_working,
                    }
                out.append(woDict)
        return out

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
    def stopWork(self, workorder, n_pieces=0):
        if not workorder:
            return False
        woLine = self.browse(self.listify(workorder))
        for woBrws in woLine:
            if n_pieces == woBrws.qty_production:
                woBrws.record_production()
                return woBrws.button_finish()
        return False
        

