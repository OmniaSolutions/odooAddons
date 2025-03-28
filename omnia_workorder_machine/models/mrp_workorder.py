'''
Created on Sep 17, 2018

@author: daniel
'''
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
import logging
import pytz
import odoo
from datetime import datetime


class MrpProductionWCLine(models.Model):
    _inherit = 'mrp.workorder'
    
    user_ids = fields.Many2many('res.users', string='Users')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    
    def _getWorkOrderDict(self):
        return {
               'wo_id': self.id,
               'wo_name': self.name,
               'wo_description': '',
               'production_name': self.production_id.name,
               'product_name': self.product_id.name,
               'product_default_code': self.product_id.default_code or '',
               'wo_state': self.state,
               'qty': "%s %s" %(self.component_remaining_qty or self.qty_remaining, self.product_uom_id.name),
               'date_planned': self.formatDatetimeTimezone(self.cleanDT(self.date_planned_start)),
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
        woBrwsList = self.search(searchFilter, order='date_planned_start ASC')
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
        woBrwsList = self.search(searchFilter, order='date_planned_start ASC,id ASC')
        woBrwsList = woBrwsList.filtered(lambda x: employee_id in x.employee_ids.ids)
        user_id = self.getUserId()
        out = self.getDictWorkorder(woBrwsList.with_user(user_id).sorted('tag_ids', reverse=True))
        if listify:
            out = self.listifyForInterface(out)
        return out

    @api.model
    def getWorkordersByDomain(self, domain=[], listify=False):
        domain.append(('state', 'in', ['ready', 'progress']))
        woBrwsList = self.search(domain,
                                 order='tag_ids ASC, date_planned_start ASC,id ASC')
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

    @api.model
    def startWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            return woBrws.button_start()
        return False

    @api.model
    def pauseWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            return woBrws.button_pending()
        return False
    
    @api.model
    def resumeWork(self, workorder, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        for woBrws in woLine:
            return woBrws.button_start()
        return False
    
    @api.model
    def recordWork(self, workorder, n_pieces=0, n_scrap=0.0, user_id=0, employee_id=0):
        woLine = self.preliminaryWork(workorder, user_id, employee_id)
        ret = False
        for woBrws in woLine:
            ret = woBrws._recordWork(n_pieces,
                                     n_scrap)
        return ret

    def _recordWork(self,
                    n_pieces=0,
                    n_scrap=0.0):
        for work_order_id in self:
            if n_pieces > 0:
                if work_order_id.is_first_started_wo:
                    work_order_id.qty_producing = n_pieces
                    if n_pieces <= work_order_id.qty_remaining:
                        work_order_id.with_context(no_start_next=True).record_production()
                else:
                    work_order_id.qty_produced += n_pieces
                    if work_order_id.qty_produced >= work_order_id.qty_production:
                        work_order_id.with_context(no_start_next=True).record_production()
                    else:
                        work_order_id.end_previous()
                        work_order_id.button_start()
            elif n_pieces == 0 and not work_order_id.qty_remaining:
                work_order_id.do_finish()
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

    def getUserId(self):
        out = self.env.ref('base.user_admin').id
        try:
            out = int(self.env['ir.config_parameter'].sudo().get_param('WORKORDER_MACHINE_UID'))
        except Exception as ex:
            logging.error(ex)
        return out

    def getRecordProductionAction(self, work_order_id):
        '''
<button name="action_menu" type="object" class="btn-secondary o_workorder_icon_btn" string="" icon="fa-bars" aria-label="Dropdown menu" title="Dropdown menu"/>
<button name="button_pending" type="object" class="btn-secondary mr8" attrs="{'invisible': ['|', ('is_user_working', '=', False), ('working_state', '=', 'blocked')]}" barcode_trigger="pause" string="Pause"/>
<button name="button_start" type="object" class="btn-warning" attrs="{'invisible': ['|', '|', ('is_user_working', '=', True), ('working_state', '=', 'blocked'), ('state', '=', 'done')]}" barcode_trigger="pause" string="Continue"/>
<button name="button_unblock" type="object" context="{'default_workcenter_id': workcenter_id}" attrs="{'invisible': [('working_state', '!=', 'blocked')]}" string="Unblock" class="btn-danger"/>
<button name="action_previous" type="object" class="btn-secondary" string="Previous" icon="fa-chevron-left o_workorder_btn_icon_small" attrs="{'invisible': [('is_first_step', '=', True)]}" barcode_trigger="prev"/>
<button disabled="1" class="btn-secondary" string="Previous" icon="fa-chevron-left o_workorder_btn_icon_small" attrs="{'invisible': [('is_first_step', '=', False)]}"/>
<button name="action_skip" type="object" class="btn-secondary" string="Skip" icon="fa-chevron-right float-right o_workorder_btn_icon_small" attrs="{'invisible': [('is_last_step', '=', True)]}" barcode_trigger="skip"/>
<button disabled="1" class="btn-secondary" string="Skip" icon="fa-chevron-right float-right o_workorder_btn_icon_small" attrs="{'invisible': [('is_last_step', '=', False)]}"/>



<button name="action_next" type="object" class="btn-primary" attrs="{'invisible': ['|', ('is_user_working', '=', False),'|', ('is_last_step', '=', True), '&amp;', '|', ('quality_state', '=', 'none'), ('test_type', '!=', 'passfail'), ('test_type', '!=', 'instructions')]}" barcode_trigger="next" string="Next"/>
<button name="action_next" type="object" class="btn-secondary" attrs="{'invisible': ['|', '|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', 'not in', ['register_consumed_materials', 'register_byproducts', 'picture']), ('consumption', '=', 'strict'), '&amp;', ('consumption', 'in', ['flexible', 'warning']), ('component_qty_to_do', '&gt;=', 0)]}" barcode_trigger="next" string="VALIDATE"/>
<button name="action_next" type="object" class="btn-primary" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', 'not in', ['register_consumed_materials', 'register_byproducts', 'picture']), ('component_qty_to_do', '&lt;', 0)]}" barcode_trigger="next" string="VALIDATE"/>

<button name="action_continue" type="object" class="btn-primary" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', '!=', 'register_byproducts'), ('component_qty_to_do', '&gt;=', 0)]}" barcode_trigger="continue" string="CONTINUE PRODUCTION"/>
<button name="action_continue" type="object" class="btn-secondary" attrs="{'invisible': ['|', '|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', '!=', 'register_byproducts'), ('consumption', '=', 'strict'), '&amp;', ('consumption', 'in', ['flexible', 'warning']), ('component_qty_to_do', '&lt;', 0)]}" barcode_trigger="continue" string="CONTINUE PRODUCTION"/>
<button name="action_continue" type="object" class="btn-primary" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', '!=', 'register_consumed_materials'), ('component_qty_to_do', '&gt;=', 0)]}" barcode_trigger="continue" string="CONTINUE CONSUMPTION"/>
<button name="action_continue" type="object" class="btn-secondary" attrs="{'invisible': ['|', '|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '=', True), ('test_type', '!=', 'register_consumed_materials'), ('consumption', '=', 'strict'), '&amp;', ('consumption', 'in', ['flexible', 'warning']), ('component_qty_to_do', '&lt;', 0)]}" barcode_trigger="continue" string="CONTINUE CONSUMPTION"/>

<button name="action_print" type="object" class="btn-primary" attrs="{'invisible': [('test_type', '!=', 'print_label')]}" barcode_trigger="print" string="Print Labels"/>

<button name="record_production" type="object" string="Record production" attrs="{'invisible': ['|', '|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '!=', True), ('skipped_check_ids', '!=', []), ('is_last_unfinished_wo', '=', True), ('is_last_lot', '=', True)]}" barcode_trigger="record" class="btn-primary"/>

<button name="do_finish" type="object" string="Mark as Done" icon="fa-check" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '!=', True), ('skipped_check_ids', '!=', []), '&amp;', ('is_last_unfinished_wo', '=', False), ('is_last_lot', '=', False)]}" class="btn-primary" barcode_trigger="cloWO"/>

<button name="action_open_manufacturing_order" type="object" string="Mark as Done and Close MO" icon="fa-check" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '!=', True), ('skipped_check_ids', '!=', []), ('is_last_unfinished_wo', '=', False)]}" class="btn-primary" barcode_trigger="cloMO"/>
<button name="action_first_skipped_step" type="object" string="Finish steps" attrs="{'invisible': ['|', '|', '|', ('is_user_working', '=', False), ('is_last_step', '!=', True), ('state', '!=', 'progress'), ('skipped_check_ids', '=', [])]}" class="btn-primary" barcode_trigger="finish"/>
        '''

        if not (
            not work_order_id.is_user_working or (
                work_order_id.is_last_step or (
                    (work_order_id.quality_state == 'none' or work_order_id.test_type != 'passfail') and work_order_id.test_type != 'instructions')
                )):
            return self.action_next
        elif not (
                (
                    (   
                        (not work_order_id.is_user_working or work_order_id.is_last_step) 
                    or
                        work_order_id.test_type not in ['register_consumed_materials', 'register_byproducts', 'picture']
                    )
                or
                    work_order_id.consumption == 'strict'
                )
            or
                (
                    (work_order_id.consumption in ['flexible', 'warning'])
                and
                    (work_order_id.component_qty_to_do >= 0)
                )
            ):
            return self.action_next
        elif not (
                (
                    (not work_order_id.is_user_working or work_order_id.is_last_step)
                or 
                    (work_order_id.test_type not in ['register_consumed_materials', 'register_byproducts', 'picture'])
                )
            or
                work_order_id.component_qty_to_do < 0
            ):
            return self.action_next
        elif not (
                (
                    (not work_order_id.is_user_working or work_order_id.is_last_step)
                or
                    (work_order_id.test_type != 'register_byproducts')    
                )
            or
                work_order_id.component_qty_to_do > 0
            ):
            return self.action_continue
        elif not (
                (
                    (
                        (not work_order_id.is_user_working or work_order_id.is_last_step)
                    or
                        (work_order_id.test_type != 'register_byproducts')    
                    )
                or
                    work_order_id.consumption == 'strict'
                )
            or
                (
                    (work_order_id.consumption in ['flexible', 'warning'])
                and
                    (work_order_id.component_qty_to_do < 0)
                )
            ):
            return self.action_continue
        elif not (
                (
                    (not work_order_id.is_user_working or work_order_id.is_last_step)
                or
                    (work_order_id.test_type != 'register_consumed_materials')
                )
            or
                (work_order_id.component_qty_to_do >= 0)
            ):
            return self.action_continue
        elif not (
                (
                    (
                        (not work_order_id.is_user_working or work_order_id.is_last_step)
                    or
                        (work_order_id.test_type != 'register_consumed_materials')
                    )
                or
                    (work_order_id.consumption == 'strict')
                )
            or
                (
                    (work_order_id.consumption in ['flexible', 'warning'])
                and
                    (work_order_id.component_qty_to_do < 0)
                )
            ):
            return self.action_continue
        elif not (
                (
                    (
                        (not work_order_id.is_user_working or work_order_id.is_last_step != True)
                    or
                        work_order_id.skipped_check_ids != []
                    )
                or
                    work_order_id.is_last_unfinished_wo == True
                )
            or
                work_order_id.is_last_lot == True
            ):
            return self.record_production
        elif not (
            # '''
            # ['|', 
            #     '|', 
            #         '|',
            #             ('is_user_working', '=', False), 
            #             ('is_last_step', '!=', True), 
            #         ('skipped_check_ids', '!=', []), 
            #     '&', ('is_last_unfinished_wo', '=', False), ('is_last_lot', '=', False)]
            # '''
                (
                    (not work_order_id.is_user_working or work_order_id.is_last_step != True)
                or
                    work_order_id.skipped_check_ids != []
                )
            or
                (
                    work_order_id.is_last_unfinished_wo == False
                and
                    work_order_id.is_last_lot == False
                )
            ):
            return self.do_finish
        