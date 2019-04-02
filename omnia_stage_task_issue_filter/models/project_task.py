from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval


class ProjectIssue(models.Model):
    _inherit = "project.issue"
    _description = "Project Issue"

    @api.model
    def _get_default_stage_id(self):
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False), ('show_on_issue', '=', True)])