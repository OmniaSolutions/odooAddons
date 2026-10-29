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
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .ai_agent_provider_client import AiProviderApiError, AiProviderAuthError, list_models

PROVIDER_SELECTION = [
    ('anthropic', 'Claude (Anthropic)'),
    ('openai', 'ChatGPT (OpenAI)'),
    ('google', 'Gemini (Google)'),
    ('groq', 'Groq'),
]


class AiAgentProviderAccount(models.Model):
    _name = 'ai.agent.provider.account'
    _description = 'AI Agent Provider Account'
    _rec_name = 'provider'

    provider = fields.Selection(PROVIDER_SELECTION, required=True, default='anthropic')
    api_token = fields.Char(string="API Token", groups="base.group_system")
    active = fields.Boolean(default=True)
    model_ids = fields.One2many('ai.agent.model', 'account_id', string="Models")
    default_model_id = fields.Many2one(
        'ai.agent.model',
        string="Default Model",
        domain="[('account_id', '=', id)]",
        help="Used when a Server Action or Report doesn't pick a model itself.",
    )
    last_fetch_date = fields.Datetime(string="Last Refreshed", readonly=True)

    @api.model
    def _get_default_account(self):
        """The one account record to use everywhere, resolved the same
        way every time so every caller lands on the same record."""
        account = self.env.ref(
            'omnia_report_ai_agent.ai_agent_provider_account_default', raise_if_not_found=False
        )
        if not account:
            account = self.search([], limit=1)
        if not account:
            account = self.create({'provider': 'anthropic'})
        return account

    def action_test_connection(self):
        """Lightweight check that the token still authenticates, without
        touching ai.agent.model. Always a plain notification, never a
        blocking validation."""
        self.ensure_one()
        try:
            list_models(self.provider, self.api_token)
        except (AiProviderAuthError, AiProviderApiError) as exc:
            raise UserError(str(exc)) from exc
        if not self.default_model_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Connection successful"),
                    'message': _('The API token works. Click "Fetch Models" and pick one to finish setup.'),
                    'type': 'warning',
                    'sticky': True,
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Connection successful"),
                'message': _("The API token is valid."),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_fetch_models(self):
        """Sync ai.agent.model with the provider's model list: create new
        ones, refresh names, archive (never delete) ones no longer listed."""
        self.ensure_one()
        try:
            fetched = list_models(self.provider, self.api_token)
        except (AiProviderAuthError, AiProviderApiError) as exc:
            raise UserError(str(exc)) from exc

        model_obj = self.env['ai.agent.model'].with_context(active_test=False)
        existing = {m.model_code: m for m in model_obj.search([
            ('account_id', '=', self.id),
            ('provider', '=', self.provider),
        ])}
        seen_codes = set()
        for item in fetched:
            seen_codes.add(item['code'])
            if item['code'] in existing:
                record = existing[item['code']]
                if record.confirmed_unavailable:
                    continue
                vals = {'name': item['name']}
                if not record.active:
                    vals['active'] = True
                record.write(vals)
            else:
                model_obj.create({
                    'account_id': self.id,
                    'provider': self.provider,
                    'name': item['name'],
                    'model_code': item['code'],
                })
        stale_codes = set(existing) - seen_codes
        if stale_codes:
            model_obj.search([
                ('account_id', '=', self.id),
                ('provider', '=', self.provider),
                ('model_code', 'in', list(stale_codes)),
            ]).write({'active': False})
        self.last_fetch_date = fields.Datetime.now()

        active_models = self.env['ai.agent.model'].search([
            ('account_id', '=', self.id),
            ('provider', '=', self.provider),
            ('active', '=', True),
        ])
        if not self.default_model_id or self.default_model_id not in active_models:
            self.default_model_id = active_models[:1]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Models refreshed"),
                'message': _("%(count)s model(s) found.") % {'count': len(fetched)},
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }
