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


    # @api.model
    # def getWorkordersByUser(self, user_id, listify=False):
    #     employee_id = int(user_id)
    #     if employee_id == 0:
    #         return []
    #     searchFilter = [('state', 'in', ['ready', 'progress'])]
    #     logging.info('Getting Work Orders with search %r' % (searchFilter))
    #     woBrwsList = self.search(searchFilter, order='date_planned_start ASC,id ASC')
    #     woBrwsList = woBrwsList.filtered(lambda x: employee_id in x.employee_ids.ids)
    #     out = self.getDictWorkorder(woBrwsList)
    #     if listify:
    #         out = self.listifyForInterface(out)
    #     return out
    #
    # def getUserId(self):
    #     out = self.env.ref('base.user_admin').id
    #     try:
    #         out = int(self.env['ir.config_parameter'].sudo().get_param('WORKORDER_MACHINE_UID'))
    #     except Exception as ex:
    #         logging.error(ex)
    #     return out
    #
    # @api.model
    # def startWork(self, workorder):
    #     user = self.getUserId()
    #     return super(MrpProductionWCLine, self.with_user(user)).startWork(workorder)
    #
    # @api.model
    # def pauseWork(self, workorder):
    #     user = self.getUserId()
    #     return super(MrpProductionWCLine, self.with_user(user)).pauseWork(workorder)
    #
    # @api.model
    # def resumeWork(self, workorder):
    #     user = self.getUserId()
    #     return super(MrpProductionWCLine, self.with_user(user)).resumeWork(workorder)
    #
    # @api.model
    # def recordWork(self, workorder, n_pieces=0, n_scrap=0.0):
    #     user = self.getUserId()
    #     return super(MrpProductionWCLine, self.with_user(user)).recordWork(workorder, n_pieces, n_scrap)
