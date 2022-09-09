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


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    
    def _prepare_timeline_vals(self, duration, date_start, date_end=False):
        ret = super(MrpWorkorder, self)._prepare_timeline_vals(duration, date_start, date_end)
        employee_mrp_id = self.env.context.get('employee_mrp_id')
        if employee_mrp_id:
            ret['employee_mrp_id'] = employee_mrp_id
        return ret
