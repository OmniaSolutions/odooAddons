# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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
import os
import csv
import logging
import datetime
#
from openerp.osv.osv import except_osv as UserError
from openerp import models
from openerp import fields
from openerp import _
from openerp import osv
from openerp import api


class product_product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def fix_workflows(self):
        ids = self.env.context.get('active_ids', [])
        for product_id in self.browse(ids):
            res_id = product_id.id
            wkf_inst = self.get_wkf_instance(self._name, res_id)
            inst_id  = wkf_inst.id
            prod_state = product_id.state or 'draft'
            expected_activity = False
            if inst_id:
                expected_activity = self.get_wkf_activity_expected(prod_state, wkf_inst.wkf_id.id)
                wkf_workitem = self.get_wkf_workitem(inst_id)
                if wkf_workitem:
                    wkf_activity = self.get_wkf_activity(wkf_workitem.act_id.id, wkf_inst.wkf_id.id)
                    if not wkf_activity:
                        raise UserError('Error', 'Cannot find correct activity id')
                    elif wkf_activity.id != expected_activity.id:
                        self.update_wkf_workitem(wkf_workitem, {
                            'act_id': expected_activity.id
                            })
                else:
                    wkf_workitem = self.create_wkf_workitem(expected_activity.id, wkf_inst.id)
            else:
                wkf_id = self.get_wkf_id('product.product')
                inst_id = self.create_wkf_instance('product.product', wkf_id, res_id)
                expected_activity = self.get_wkf_activity_expected(product_id.state, inst_id.wkf_id)
                wkf_workitem = self.create_wkf_workitem(expected_activity.id, inst_id.id)
            self.update_wkf_instance(wkf_inst, prod_state)

    @api.model
    def create_wkf_instance(self, model, wkf_id, res_id):
        vals = {
            'res_type': model,
            'uid': self.env.uid,
            'wkf_id': wkf_id,
            'state': 'active',
            'res_id': res_id,
            }
        new = self.env['workflow.instance'].create(vals)
        return new

    @api.model
    def get_wkf_id(self, model):
        wkf_id = self.env['workflow'].search([
            ('osv', '=', model)
            ])
        return wkf_id[0]

    @api.model
    def get_wkf_instance(self, model, res_id):
        wkf_instance = self.env['workflow.instance'].search([
            ('res_type', '=', model),
            ('res_id', '=', res_id)
            ])
        for obj in wkf_instance:
            return obj
        return False

    @api.model
    def create_wkf_workitem(self, act_id, inst_id):
        vals = {
            'act_id': act_id,
            'inst_id': inst_id,
            'state': 'complete',
            }
        new = self.env['workflow.workitem'].create(vals)
        return new

    @api.model
    def update_wkf_instance(self, item, state):
        if not item:
            return
        item.write({'state': 'active'})

    @api.model
    def update_wkf_workitem(self, item, vals):
        item.write(vals)

    @api.model
    def get_wkf_workitem(self, inst_id):
        wkf_workitem = self.env['workflow.workitem'].search([
            ('inst_id', '=', inst_id)
            ])
        for obj in wkf_workitem:
            return obj
        return False

    @api.model
    def get_wkf_activity(self, act_id, wkf_id):
        wkf_activity = self.env['workflow.activity'].search([
            ('id', '=', act_id),
            ('wkf_id', '=', wkf_id)
            ])
        for obj in wkf_activity:
            return obj
        return False

    @api.model
    def get_wkf_activity_expected(self, state, wkf_id):
        wkf_activity = self.env['workflow.activity'].search([
            ('name', '=', state),
            ('wkf_id', '=', wkf_id)
            ])
        return wkf_activity

