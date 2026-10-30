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


class AiReportAgentWizardLine(models.TransientModel):
    _name = 'ai.report.agent.wizard.line'
    _description = 'AI Report Agent Wizard Result'

    wizard_id = fields.Many2one('ai.report.agent.wizard', required=True, ondelete='cascade')
    res_model = fields.Char()
    res_id = fields.Integer()
    record_display_name = fields.Char()
    generated_text = fields.Text()
    verification_notes = fields.Text(
        help="Result of the second AI pass that checks every number/name/date the report "
             "states against the real record data. \"No discrepancies found.\" when clean, "
             "otherwise one line per mismatch found.",
    )
