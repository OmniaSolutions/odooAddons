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
        """The one account record to use everywhere (Settings page, the
        wizard, ...). Always resolved the same way so every caller lands on
        the exact same record -- never a plain search() by itself, which
        could silently return a different, stray record if more than one
        ever ends up existing (e.g. one created by this same fallback before
        the seeded one existed)."""
        account = self.env.ref(
            'omnia_report_ai_agent.ai_agent_provider_account_default', raise_if_not_found=False
        )
        if not account:
            account = self.search([], limit=1)
        if not account:
            account = self.create({'provider': 'anthropic'})
        return account

    def action_test_connection(self):
        """Lightweight check that the token still authenticates -- does not
        touch ai.agent.model, unlike Fetch Models.

        Note: this is a plain notification, never a blocking validation. A
        hard constraint here used to deadlock the form: clicking any button
        (Save, Fetch Models, Test Connection) makes Odoo save pending field
        changes first, and "token set but no model fetched yet" is a normal,
        necessary in-between state -- not something that should block saving
        or fetching."""
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
        """Call the provider's list-models endpoint and sync ai.agent.model:
        new models are created, known active ones get their name refreshed,
        and models the provider no longer lists get archived (never
        deleted, since Default Model or a Server Action might already
        point at one)."""
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
