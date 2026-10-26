# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2026 https://OmniaSolutions.website
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(
        selection_add=[('ai_agent_report', 'AI Agent Report')],
        ondelete={'ai_agent_report': 'cascade'},
    )

    def _run_action_ai_agent_report_multi(self, eval_context=None):
        """Open the AI Report Agent wizard on whichever record(s) this
        action is running on -- one or several selected at once. The wizard
        (not this action) collects the command, instructions and
        attachments, applying them to every record; the AI model itself
        isn't asked here either, it's fixed once in Settings > AI Agent."""
        self.ensure_one()
        active_model = self._context.get('active_model') or self.model_name
        active_ids = self._context.get('active_ids')
        if not active_ids and self._context.get('active_id'):
            active_ids = [self._context['active_id']]
        return {
            'name': "Generate Report with AI Agent",
            'type': 'ir.actions.act_window',
            'res_model': 'ai.report.agent.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': active_model,
                'default_res_ids': ",".join(str(i) for i in (active_ids or [])),
            },
        }
