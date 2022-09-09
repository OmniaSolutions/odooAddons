from odoo import models
from odoo import fields
from odoo import _


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_mrp_id = fields.Many2one('hr.employee', _('Employee'))