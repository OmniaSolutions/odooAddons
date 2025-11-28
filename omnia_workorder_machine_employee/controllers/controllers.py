'''
Created on Oct 14, 2018

@author: daniel
'''
import logging
import json
import os
import base64
from odoo import _
from odoo import http
from odoo.http import request
from odoo.http import Response
from odoo.http import Controller

from odoo.addons.omnia_workorder_machine.controllers.controllers import WebsiteWorkorderControllerByUser

import tempfile


class WebsiteWorkorderControllerByEmployee(WebsiteWorkorderControllerByUser):

    @http.route('/mrp_omnia/workorder_by_employee')
    def workorderByEmployee(self, **post):
        logging.info('WorkorderMachine called')
        values = post
        values['hide_user'] = True
        return self.renderTemplate('omnia_workorder_machine.by_user', values)

    @http.route('/mrp_omnia/submit_popup_workorder', type='json', auth='public')
    def submit_popup_workorder(self, workorder=None, **kwargs):
        Workorder = request.env['mrp.workorder'].sudo()
        try:
            user_id = int(kwargs.get("user_id", 0))
            employee_id = int(kwargs.get("employee_id", 0))
            for wo in workorder:
                try:
                    wo_id = int(wo.get('wo_id') or 0)
                except:
                    continue
                duration_str = wo.get('duration', "00:00")
                try:
                    hours, minutes = map(int, duration_str.split(':'))
                    duration_hours = (hours * 60 + minutes) / 60.0
                except:
                    duration_hours = 0.0

                qty_to_produce = float(wo.get('qty') or 0)
                scrap = float(wo.get('scrap') or 0)

                record = Workorder.search([('id', '=', wo_id)], limit=1)
                if not record:
                    continue
                record.write({'duration': duration_hours})
                if qty_to_produce > 0:
                    Workorder.recordWork(
                        wo_id,
                        qty_to_produce,
                        scrap,
                        user_id,
                        employee_id
                    )
                else:
                    _logger.info(f"WO {wo_id}: 0 qty provided, skipping production")


            return {'success': True, 'message': 'Workorders updated'}

        except Exception as e:
            _logger.error("Error in submit_popup_workorder: %s", e)
            return {'success': False, 'message': str(e)}
