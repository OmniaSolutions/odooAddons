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
from odoo import _, fields, models


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(
        selection_add=[('ai_agent_report', 'AI Agent Report')],
        ondelete={'ai_agent_report': 'cascade'},
    )
    ai_agent_command = fields.Char(
        string="Command",
        help="Predefined command the AI agent runs with every time, with no "
             "prompt shown to the user. Leave empty to ask for one in the "
             "wizard each time instead.",
    )
    ai_agent_instructions = fields.Text(
        string="Instructions",
        help="Predefined, detailed instructions sent to the AI agent every time.",
    )
    ai_agent_attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments",
        help="Source files the AI agent should always read for this action.",
    )

    def _run_action_ai_agent_report_multi(self, eval_context=None):
        """
        Run the AI Report Agent on whichever record(s) this action is
        running on -- one or several selected at once -- using the Command/
        Instructions/Attachments predefined here (admin-only, same as any
        other Server Action field), and open straight on the Preview.
        """
        self.ensure_one()
        active_model = self._context.get('active_model') or self.model_name
        active_ids = self._context.get('active_ids')
        if not active_ids and self._context.get('active_id'):
            active_ids = [self._context['active_id']]
        wizard = self.env['ai.report.agent.wizard'].create({
            'res_model': active_model,
            'res_ids': ",".join(str(i) for i in (active_ids or [])),
            'command': self.ai_agent_command,
            'instructions': self.ai_agent_instructions,
            'attachment_ids': [(6, 0, self.ai_agent_attachment_ids.ids)],
        })
        wizard.action_generate()
        return {
            'name': _("Report Preview"),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.report.agent.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
