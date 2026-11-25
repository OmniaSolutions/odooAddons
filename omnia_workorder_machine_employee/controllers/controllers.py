# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from odoo import http
from odoo.http import request

from odoo.addons.omnia_workorder_machine.controllers.controllers import WebsiteWorkorderControllerByUser


class WebsiteWorkorderControllerByEmployee(WebsiteWorkorderControllerByUser):

    @http.route('/mrp_omnia/workorder_by_employee')
    def workorderByEmployee(self, **post):
        values = post
        values['hide_user'] = True
        return self.renderTemplate('omnia_workorder_machine.by_user', values)

    @http.route('/mrp_omnia/submit_popup_workorder', type='json', auth='public')
    def submit_popup_workorder(self, workorder=None, **kwargs):
        Workorder = request.env['mrp.workorder'].sudo()
        try:
            user_id = int(kwargs.get("user_id", 0))
            employee_id = int(kwargs.get("employee_id", 0))
            total_time_computation = 0.0
            total_item_produced = 0.0
            workorder_time_to_set={}
            for wo in workorder:
                try:
                    wo_id = int(wo.get('wo_id') or 0)
                except:
                    continue
                qty_to_produce = float(wo.get('qty') or 0)
                scrap = float(wo.get('scrap') or 0)
                record = Workorder.search([('id', '=', wo_id)], limit=1)
                if not record:
                    continue
                if qty_to_produce > 0:
                    Workorder.recordWork(
                        wo_id,
                        qty_to_produce,
                        scrap,
                        user_id,
                        employee_id
                    )
                    total_time_computation+=record.getLastComputationTime()
                    total_item_produced+=qty_to_produce
                    workorder_time_to_set[record]=qty_to_produce
                else:
                    logging.info(f"WO {wo_id}: 0 qty provided, skipping production")
            if total_time_computation:
                time_for_single_item = total_time_computation/total_item_produced
                for w_idm, qty in workorder_time_to_set.items():
                    w_idm.adjust_last_recorded(qty*time_for_single_item)

            return {'success': True, 'message': 'Workorders updated'}

        except Exception as e:
            logging.error("Error in submit_popup_workorder: %s", e)
            return {'success': False, 'message': str(e)}
