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

from .ai_agent_provider_account import PROVIDER_SELECTION


class AiAgentModel(models.Model):
    _name = 'ai.agent.model'
    _description = 'AI Agent Model'
    _order = 'sequence, id'
    _sql_constraints = [
        ('model_code_account_uniq', 'unique(account_id, model_code)',
         'This model is already listed for this provider account.'),
    ]

    account_id = fields.Many2one(
        'ai.agent.provider.account',
        string="Provider Account",
        required=True,
        ondelete='cascade',
        help="Which provider credential this model was fetched from.",
    )
    provider = fields.Selection(PROVIDER_SELECTION, required=True)
    name = fields.Char(
        required=True,
        help="Label shown when picking a model, e.g. 'Claude Sonnet 5.5'.",
    )
    model_code = fields.Char(
        required=True,
        help="Technical model identifier sent to the provider's API, e.g. 'claude-sonnet-5-5'.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(
        default=True,
        help="Unchecking this hides the model from the AI Report Agent wizard without deleting it. "
             "Fetching models again also unchecks models the provider no longer lists.",
    )
    confirmed_unavailable = fields.Boolean(
        help="Set when generating a report with this model actually got rejected by the "
             "provider (e.g. HTTP 404), not just \"not seen\" in a models list. Some providers "
             "(Gemini, notably) keep listing a model that no longer works for a given key, so "
             "Fetch Models won't trust \"still listed\" to reactivate one of these -- an archived "
             "model with this unset is assumed to simply have been missing from one fetch and is "
             "fair game to reactivate the next time it's listed again.",
    )
