from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval


class Task(models.Model):
    _inherit = "project.task"
    _description = "Task"

    @api.model
    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False), ('show_on_issue', '=', True)])