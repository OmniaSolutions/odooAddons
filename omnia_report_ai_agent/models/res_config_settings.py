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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_agent_account_id = fields.Many2one(
        'ai.agent.provider.account',
        default=lambda self: self.env['ai.agent.provider.account']._get_default_account(),
    )
    ai_agent_provider = fields.Selection(
        related='ai_agent_account_id.provider', readonly=False, required=True, string="Provider",
    )
    ai_agent_api_token = fields.Char(
        related='ai_agent_account_id.api_token', readonly=False,
        groups="base.group_system", string="API Token",
    )
    ai_agent_default_model_id = fields.Many2one(
        related='ai_agent_account_id.default_model_id', readonly=False, string="Default Model",
    )
    ai_agent_last_fetch_date = fields.Datetime(
        related='ai_agent_account_id.last_fetch_date', string="Last Refreshed",
    )

    @api.onchange('ai_agent_provider')
    def _onchange_ai_agent_provider(self):
        """The domain on ai_agent_default_model_id only restricts what can be
        picked -- it doesn't clear an already-selected value on its own, so
        switching AI Tool would otherwise leave the old provider's model
        showing. Jump to a model already fetched for the new provider if
        there is one, else leave it blank (never a stale, mismatched model)."""
        if not self.ai_agent_account_id:
            return
        if self.ai_agent_default_model_id.provider == self.ai_agent_provider:
            return
        self.ai_agent_default_model_id = self.env['ai.agent.model'].search([
            ('account_id', '=', self.ai_agent_account_id.id),
            ('provider', '=', self.ai_agent_provider),
            ('active', '=', True),
        ], limit=1)

    def action_test_connection(self):
        self.ensure_one()
        return self.ai_agent_account_id.action_test_connection()

    def action_fetch_models(self):
        self.ensure_one()
        return self.ai_agent_account_id.action_fetch_models()
