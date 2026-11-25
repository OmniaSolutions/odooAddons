# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2019 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models
import logging
import pytz
import odoo
from datetime import timedelta


class MrpProductionWCLine(models.Model):
    _inherit = 'mrp.workorder'
    
    user_ids = fields.Many2many(comodel_name='res.users', string='Users')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    operation_note = fields.Html(string='Operation Note')
    
    def _getWorkOrderDict(self):
        return {
               'wo_id': self.id,
               'wo_name': self.name,
               'wo_description': '',
               'production_name': self.production_id.name,
               'product_name': self.product_id.name,
               'product_default_code': self.product_id.default_code or '',
               'wo_state': self.state,
               'qty': "%s / %s %s" %(self.qty_produced, self.qty_production, self.uom_id.name),
               'date_planned': self.formatDatetimeTimezone(self.cleanDT(self.date_start)),
               'is_user_working': self.is_user_working,
               }

    def cleanDT(self, dt):
        if not dt:
            return ''
        return dt.replace(microsecond=0)

    def formatDatetimeTimezone(self, value, tz=False):
        if not value:
            return ''
        if isinstance(value, str):
            timestamp = odoo.fields.Datetime.from_string(value)
        else:
            timestamp = value
        tz_name = tz or self.env.user.tz or 'UTC'
        utc_datetime = pytz.utc.localize(timestamp, is_dst=False)
        try:
            context_tz = pytz.timezone(tz_name)
            localized_datetime = utc_datetime.astimezone(context_tz)
        except Exception:
            localized_datetime = utc_datetime
        return localized_datetime.replace(tzinfo=None)

    def getDictWorkorder(self, woBrwsList):
        out = []
        for woBrws in woBrwsList:
            woBrws = woBrws.sudo()
            if woBrws.production_id.state in ['confirmed', 'planned', 'progress', 'confirm']:
                out.append(woBrws._getWorkOrderDict())
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
        woBrwsList = self.search(searchFilter, order='date_start ASC')
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
        woBrwsList = self.search(searchFilter, order='date_start ASC,id ASC')
        woBrwsList = woBrwsList.filtered(lambda x: user_id in x.user_ids.ids or x.user_id.id == user_id)
        if not user_id:
            user_id = self.getUserId()
        out = self.with_user(user_id).getDictWorkorder(woBrwsList.with_user(user_id))
        if listify:
            out = self.listifyForInterface(out)
        return out

    @api.model
    def getWorkordersByEmployee(self, employee_id, listify=False):
        employee_id = int(employee_id)
        if employee_id == 0:
            return []
        searchFilter = [('state', 'in', ['ready', 'progress'])]
        logging.info('Getting Work Orders with search %r' % (searchFilter))
        woBrwsList = self.search(searchFilter, order='date_start ASC,id ASC')
        woBrwsList = woBrwsList.filtered(lambda x: employee_id in x.employee_ids.ids)
        user_id = self.getUserId()
        out = self.getDictWorkorder(woBrwsList.with_user(user_id))
        if listify:
            out = self.listifyForInterface(out)
        return out

    @api.model
    def getWorkordersByDomain(self, domain=[], listify=False):
        domain.append(('state', 'in', ['ready', 'progress']))
        woBrwsList = self.search(domain,
                                 order='date_start ASC,id ASC')
        user_id = self.getUserId()
        out = self.getDictWorkorder(woBrwsList.with_user(user_id))
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
                    str(r"/mrp_omnia/get_worksheet/" + str(dictRes.get('wo_id', ''))),
                ])
        return lines

    def listify(self, val):
        if isinstance(val, (list, tuple)):
            return val
        elif isinstance(val, (int, float)):
            return [val]
        return []

    @api.model
    def preliminaryWork(self,
                        workorder,
                        user_id=0,
                        employee_id=0):
        if not workorder:
            return False
        woLine = self.browse(self.listify(workorder))
        if not user_id:
            user_id = self.getUserId()
        woLine = woLine.with_user(user_id)
        if employee_id:
            if employee_id not in woLine.employee_ids.ids:
                woLine.employee_ids =[(6,0,[employee_id])]
            woLine = woLine.with_context(employee_mrp_id=employee_id)
        return woLine

    def _start_user_timer(self):
        """Open a productivity-timeline entry keyed on the current
        (possibly impersonated) res.users, for flows that have no
        hr.employee at all (e.g. the plain "by user" page), since
        button_start(bypass=True) skips Odoo's own start_employee()
        and is_user_working is computed from an open time_ids entry
        whose user_id matches self.env.user.
        """
        self.ensure_one()
        if self.time_ids.filtered(lambda t: not t.date_end and t.user_id.id == self.env.user.id):
            return
        if not self.duration_expected or self.duration <= self.duration_expected:
            loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
        else:
            loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')], limit=1)
        if not loss:
            return
        self.env['mrp.workcenter.productivity'].create({
            'workorder_id': self.id,
            'workcenter_id': self.workcenter_id.id,
            'description': "Time Tracking: %s" % self.env.user.name,
            'loss_id': loss.id,
            'date_start': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'company_id': self.company_id.id,
        })

    def _stop_user_timer(self):
        """Counterpart of _start_user_timer(): closes this user's own
        open timer entry, since button_pending()'s native stop_employee()
        only closes entries matching self.env.user.employee_id.
        """
        self.ensure_one()
        open_timers = self.time_ids.filtered(lambda t: not t.date_end and t.user_id.id == self.env.user.id)
        open_timers._close()

    def _restart_after_partial(self):
        """button_start() equivalent used when _recordWork() continues a
        workorder after a partial quantity. Same bypass=True reasoning as
        startWork()/resumeWork(): skip Odoo's hr.employee-link requirement
        and drive the timer ourselves, via the real hr.employee when this
        call came in with one (context key set by preliminaryWork()), or
        via the impersonated res.users otherwise.
        """
        self.ensure_one()
        self.button_start(bypass=True)
        employee_id = self.env.context.get('employee_mrp_id')
        if employee_id:
            self.start_employee(employee_id)
        else:
            self._start_user_timer()

    @api.model
    def startWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            res = woBrws.button_start(bypass=True)
            if employee_id:
                woBrws.start_employee(employee_id)
            else:
                woBrws._start_user_timer()
            return res
        return False

    @api.model
    def pauseWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            res = woBrws.button_pending()
            if not employee_id:
                woBrws._stop_user_timer()
            return res
        return False

    @api.model
    def resumeWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            res = woBrws.button_start(bypass=True)
            if employee_id:
                woBrws.start_employee(employee_id)
            else:
                woBrws._start_user_timer()
            return res
        return False
    
    @api.model
    def recordWork(self, workorder, n_pieces=0, n_scrap=0.0, user_id=0, employee_id=0, operation_note=None):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        ret = False
        for woBrws in woLine:
            ret = woBrws._recordWork(n_pieces,
                                     n_scrap,
                                     operation_note)
        return ret

    def _recordWork(self,
                    n_pieces=0,
                    n_scrap=0.0,
                    operation_note=None):
        if operation_note is not None:
            self.operation_note = operation_note
        for work_order_id in self:
            if n_pieces > 0:
                if work_order_id.is_first_started_wo:
                    if n_pieces >= work_order_id.qty_remaining:
                        work_order_id.qty_produced += n_pieces
                        work_order_id.qty_producing = work_order_id.qty_produced
                        work_order_id.with_context(no_start_next=True).record_production()
                    elif n_pieces > 0:
                        work_order_id.qty_produced += n_pieces
                        work_order_id.end_previous()
                        work_order_id._restart_after_partial()
                else:
                    work_order_id.qty_produced += n_pieces
                    if work_order_id.qty_produced >= work_order_id.qty_production:
                        work_order_id.qty_producing = work_order_id.qty_produced
                        work_order_id.with_context(no_start_next=True).record_production()
                    else:
                        work_order_id.end_previous()
                        work_order_id._restart_after_partial()
            elif n_pieces == 0 and not work_order_id.qty_remaining:
                work_order_id.do_finish()
            if n_scrap > 0:
                work_order_id.o_do_scrap(n_scrap)
        return False
    
    def getLastCloseProductivity(self):
        timeline_obj = self.env['mrp.workcenter.productivity']
        domain = [('workorder_id', 'in', self.ids),
                  ('user_id', '=', self.getUserId()),
                  ('date_end','!=', False)]
        
        for timeline in timeline_obj.search(domain, order='id desc', limit=1):
            return timeline
        return []

    def getLastComputationTime(self):
        for timeline in self.getLastCloseProductivity():
            delta = timeline.date_end-timeline.date_start
            return delta.total_seconds()
        return 0,0
    
    def adjust_last_recorded(self, added_seconds):
        for timeline in self.getLastCloseProductivity():
            timeline.date_end = timeline.date_start + timedelta(seconds=added_seconds)

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

    def getUserId(self):
        out = self.env.ref('base.user_admin').id
        try:
            out = int(self.env['ir.config_parameter'].sudo().get_str('WORKORDER_MACHINE_UID'))
        except Exception as ex:
            logging.error(ex)
        return out
