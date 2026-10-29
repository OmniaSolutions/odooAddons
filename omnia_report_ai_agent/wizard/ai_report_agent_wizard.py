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
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.ai_agent_attachment_utils import describe_attachments
from ..models.ai_agent_field_utils import get_record_context
from ..models.ai_agent_provider_client import (
    AiProviderApiError,
    AiProviderAuthError,
    AiProviderModelUnavailableError,
    generate_text,
)

IMAGE_CAPABLE_PROVIDERS = ('anthropic', 'google')


class AiReportAgentWizard(models.TransientModel):
    _name = 'ai.report.agent.wizard'
    _description = 'AI Report Agent Wizard'

    res_model = fields.Char(string="Related Document Model")
    res_ids = fields.Char(
        string="Related Document Ids",
        help="Comma-separated ids of the record(s) this wizard runs on.",
    )
    server_action_id = fields.Many2one(
        'ir.actions.server',
        string="Server Action",
        readonly=True,
        help="The Server Action this wizard was run from -- its Command/"
             "Instructions are read from there, not duplicated here.",
    )
    result_ids = fields.One2many('ai.report.agent.wizard.line', 'wizard_id', string="Results")
    preview_html = fields.Html(string="Preview", compute='_compute_preview_html', sanitize=False)

    @api.depends('result_ids')
    def _compute_preview_html(self):
        for wizard in self:
            if not wizard.result_ids or not isinstance(wizard.id, int):
                wizard.preview_html = False
                continue
            url = "/report/html/omnia_report_ai_agent.report_ai_agent_document/%s" % wizard.id
            wizard.preview_html = (
                '<iframe src="%s" style="width: 100%%; height: 70vh; border: 0;"/>' % url
            )

    def _get_records(self):
        self.ensure_one()
        if not self.res_model or not self.res_ids:
            return self.env[self.res_model or 'base'].browse()
        ids = [int(i) for i in self.res_ids.split(',') if i.strip()]
        return self.env[self.res_model].browse(ids).exists()

    def _slugify_command(self):
        """A short, filesystem-safe filename derived from the Command text,
        used when there's more than one record and so no single record name
        to build the filename from."""
        self.ensure_one()
        command = self.server_action_id.sudo().ai_agent_command
        text = re.sub(r'[^A-Za-z0-9]+', '_', command or '').strip('_')
        words = [w for w in text.split('_') if w][:6]
        return "_".join(words) or "AI_Report"

    def _get_report_filename(self):
        """<Record name>_AI_Report for one record; a short slug of the
        Command for several (there's no single record name to use then)."""
        self.ensure_one()
        if len(self.result_ids) == 1:
            name = self.result_ids.record_display_name or "Report"
            for char in '/\\[]:*?"<>|':
                name = name.replace(char, '')
            name = " ".join(name.split()) or "Report"
            return "%s_AI_Report" % name
        return self._slugify_command()

    def _build_prompt(self, record, attachment_text=''):
        """Command + instructions (read from server_action_id) + the
        record's own data + any readable attachment text, in that order."""
        self.ensure_one()
        server_action = self.server_action_id.sudo()
        parts = [
            "Format your entire answer as plain HTML fragments only (no Markdown, no code "
            "fences, no <html>/<head>/<body> wrapper) -- it gets embedded directly into a PDF "
            "report as-is. Use <h2>/<h3> for section headings, a real <table> with <tr>/<th>/"
            "<td> for any tabular data, <strong> for emphasis, and <p>/<ul>/<li> for text.",
            "Every number, name, code, date, and quantity you write MUST come verbatim from "
            "the \"Record data\" below -- copy it exactly, do not round, re-sum, re-calculate, "
            "or estimate it yourself, even if the arithmetic looks simple. If a total or "
            "breakdown isn't explicitly given there, do not compute or state one -- omit it "
            "instead. Never state a fact, figure, or value that isn't explicitly present in "
            "the data below.",
        ]
        if server_action.ai_agent_command:
            parts.append("Task: %s" % server_action.ai_agent_command)
        if server_action.ai_agent_instructions:
            parts.append("Instructions: %s" % server_action.ai_agent_instructions)
        record_context = get_record_context(record)
        if record_context:
            parts.append("Record data:\n%s" % record_context)
        if attachment_text:
            parts.append("Attachments:\n%s" % attachment_text)
        return "\n\n".join(parts)

    def _generate_with_fallback(self, account, prompt, images=None):
        """Try the default model; on AiProviderModelUnavailableError, archive
        it and retry the next active one instead of failing outright.
        account is sudo() -- admin-only AI config any wizard user may use."""
        model = account.default_model_id
        tried_ids = []
        while model:
            try:
                return generate_text(account.provider, account.api_token, model.model_code, prompt, images=images)
            except AiProviderModelUnavailableError:
                tried_ids.append(model.id)
                model.write({'active': False, 'confirmed_unavailable': True})
                model = self.env['ai.agent.model'].sudo().search([
                    ('account_id', '=', account.id),
                    ('active', '=', True),
                    ('id', 'not in', tried_ids),
                ], limit=1)
                account.default_model_id = model
            except (AiProviderAuthError, AiProviderApiError) as exc:
                raise UserError(str(exc)) from exc
        raise UserError(_(
            "None of the fetched models for this provider are currently available. "
            "Click \"Fetch Models\" again in Settings > AI Agent, or switch AI Tool."
        ))

    def action_generate(self):
        """Call the AI once per record and store the results -- run
        automatically right after this wizard is created, with no manual
        "Generate" step or prompt screen."""
        self.ensure_one()
        account = self.env['ai.agent.provider.account'].sudo()._get_default_account()
        if not account or not account.api_token:
            raise UserError(_("Set up the AI Agent in Settings > AI Agent first."))
        if not account.default_model_id:
            raise UserError(_(
                "Pick a Default Model in Settings > AI Agent (click \"Fetch Models\" if the "
                "list is still empty) before generating a report."
            ))

        records = self._get_records()
        if not records:
            raise UserError(_("No record found to generate a report for."))

        attachments = self.server_action_id.sudo().ai_agent_attachment_ids
        attachment_text, attachment_images = describe_attachments(attachments) if attachments else ('', [])
        if attachment_images and account.provider not in IMAGE_CAPABLE_PROVIDERS:
            attachment_text += (
                "\n\n%d image attachment(s) were provided but this AI Tool doesn't support "
                "reading images, so they were not included." % len(attachment_images)
            )
            attachment_images = []

        self.result_ids.unlink()
        for record in records:
            prompt = self._build_prompt(record, attachment_text)
            text = self._generate_with_fallback(account, prompt, images=attachment_images)
            self.env['ai.report.agent.wizard.line'].create({
                'wizard_id': self.id,
                'res_model': record._name,
                'res_id': record.id,
                'record_display_name': record.display_name,
                'generated_text': text,
            })

    def action_print(self):
        """Print the report and save a copy as a normal attachment on each
        record it covers, instead of only existing inside this transient
        wizard until it's purged."""
        self.ensure_one()
        report = self.env.ref('omnia_report_ai_agent.action_report_ai_agent')
        pdf_content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
            'omnia_report_ai_agent.report_ai_agent_document', self.ids
        )
        filename = "%s.pdf" % self._get_report_filename()
        for result in self.result_ids:
            record = self.env[result.res_model].browse(result.res_id)
            if not record.exists():
                continue
            self.env['ir.attachment'].create({
                'name': filename,
                'raw': pdf_content,
                'res_model': result.res_model,
                'res_id': result.res_id,
                'mimetype': 'application/pdf',
            })
        return report.report_action(self)
