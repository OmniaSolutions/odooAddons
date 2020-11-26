'''
Created on 16 Jan 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class ProjectProject(models.Model):
    _inherit = ['project.project']

    def _compute_manufacturing_orders_count(self):
        production_obj = self.env['mrp.production']
        for project in self:
            project.man_orders_count = production_obj.search_count([
                ('project_id', '=', self.id)
                ])

    @api.model
    def relatedManufacturingOrders(self, project_brws, additional_filter=[]):
        production_obj = self.env['mrp.production']
        man_filter = [('project_id', '=', project_brws.id)]
        for element in additional_filter:
            man_filter.append(element)
        return production_obj.search(man_filter)
        
    def _compute_manufacturing_completed(self):
        """
        compute completed manufacturing orders related to this project
        """
        for project_brws in self:
            completed_man_orders = self.relatedManufacturingOrders(project_brws, [('state', 'in', ['done', 'cancel'])])
            if project_brws.man_orders_count > 0:
                project_brws.man_orders_completed = round(100.0 * (len(completed_man_orders.ids) / float(project_brws.man_orders_count)), 2)
            else:
                project_brws.man_orders_completed = 100
            

    man_orders_count = fields.Integer(compute='_compute_manufacturing_orders_count', string="Number of manufacturing orders attached")
    man_orders_completed = fields.Float(string=_('Manufacturing Completed'),
                             compute="_compute_manufacturing_completed")

    @api.multi
    def production_tree_view(self):
        self.ensure_one()
        domain = [('project_id', '=', self.id)]
        return {
            'name': _('Production Orders'),
            'domain': domain,
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }
