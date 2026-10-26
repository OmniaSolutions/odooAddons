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

from ..models.ai_agent_provider_client import (
    AiProviderApiError,
    AiProviderAuthError,
    AiProviderModelUnavailableError,
    generate_text,
)


_SKIP_FIELD_NAMES = {'id', 'display_name', '__last_update', 'create_date', 'write_date', 'create_uid', 'write_uid'}
_SKIP_FIELD_PREFIXES = ('message_', 'activity_', 'access_', 'website_')


class AiReportAgentWizard(models.TransientModel):
    _name = 'ai.report.agent.wizard'
    _description = 'AI Report Agent Wizard'

    res_model = fields.Char(string="Related Document Model")
    res_ids = fields.Char(
        string="Related Document Ids",
        help="Comma-separated ids of the record(s) this wizard runs on.",
    )
    command = fields.Char(
        string="Command",
        help="A short, one-line description of what this report should do.",
    )
    instructions = fields.Text(
        string="Instructions",
        help="Detailed instructions for the AI agent.",
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments",
        help="Source files the AI agent should read.",
    )
    result_ids = fields.One2many('ai.report.agent.wizard.line', 'wizard_id', string="Results")
    state = fields.Selection(
        [('draft', 'Draft'), ('preview', 'Preview')], default='draft', required=True,
    )
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

    def _describe_fields(self, record, inline=False):
        """One line per plain (non-binary, non-x2many) field with a value."""
        parts = []
        for fname, field in record._fields.items():
            if fname in _SKIP_FIELD_NAMES or fname.startswith(_SKIP_FIELD_PREFIXES):
                continue
            if field.type in ('binary', 'one2many', 'many2many', 'html'):
                continue
            if field.compute and not field.store:
                continue
            try:
                value = record[fname]
            except Exception:
                continue
            if value is False or value is None or value == '':
                continue
            if field.type == 'many2one':
                value = value.display_name
            parts.append(f"{field.string}={value}" if inline else f"- {field.string}: {value}")
        return parts

    def _get_record_context(self, record):
        """Plain-text dump of one record.

        Sent to the AI alongside the command/instructions/attachments so it
        already has the record's own field values instead of having to
        re-derive them from the attachments -- fewer tokens, faster, more
        accurate than letting it guess what Odoo already knows."""
        if not record or not record.exists():
            return ""

        lines = [f"Record: {record.display_name} ({record._name}, id {record.id})"]
        lines += self._describe_fields(record)

        for fname, field in record._fields.items():
            if field.type != 'one2many':
                continue
            try:
                sub_records = record[fname]
            except Exception:
                continue
            if not sub_records:
                continue
            lines.append(f"\n{field.string}:")
            for sub in sub_records:
                parts = self._describe_fields(sub, inline=True)
                if parts:
                    lines.append("  - " + ", ".join(parts))

        lines += self._get_extra_context(record)
        return "\n".join(lines)

    def _get_extra_context(self, record):
        """A few relations that matter for reporting but aren't plain
        one2many fields on the record itself, so the generic reflection
        above can't see them -- a product's Bills of Materials, notably,
        are separate mrp.bom records looked up by product, not a field on
        the product. Add more special cases here as they come up."""
        lines = []
        if record._name in ('product.template', 'product.product') and 'mrp.bom' in self.env:
            try:
                template = record if record._name == 'product.template' else record.product_tmpl_id
                boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', template.id)])
                for bom in boms:
                    lines.append(f"\nBill of Materials {bom.display_name}:")
                    for line in bom.bom_line_ids:
                        lines.append(
                            "  - Component=%s, Quantity=%s, UoM=%s"
                            % (line.product_id.display_name, line.product_qty, line.product_uom_id.name)
                        )
            except Exception:
                pass
        return lines

    def _slugify_command(self):
        """A short, filesystem-safe filename derived from the Command text,
        used when there's more than one record and so no single record name
        to build the filename from."""
        self.ensure_one()
        text = re.sub(r'[^A-Za-z0-9]+', '_', self.command or '').strip('_')
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

    def _build_prompt(self, record):
        """Command + instructions + the record's own data, in that order.
        Attachments are not included yet -- see ai_agent_provider_client.py
        for why (text-only for now, per provider multimodal support)."""
        self.ensure_one()
        parts = [
            "Format your entire answer as plain HTML fragments only (no Markdown, no code "
            "fences, no <html>/<head>/<body> wrapper) -- it gets embedded directly into a PDF "
            "report as-is. Use <h2>/<h3> for section headings, a real <table> with <tr>/<th>/"
            "<td> for any tabular data, <strong> for emphasis, and <p>/<ul>/<li> for text."
        ]
        if self.command:
            parts.append("Task: %s" % self.command)
        if self.instructions:
            parts.append("Instructions: %s" % self.instructions)
        record_context = self._get_record_context(record)
        if record_context:
            parts.append("Record data:\n%s" % record_context)
        return "\n\n".join(parts)

    def _generate_with_fallback(self, account, prompt):
        """Try the account's default model; if it turns out to be dead (not
        every provider flags that ahead of time -- Gemini notably doesn't),
        archive it and move to the next active model instead of failing
        outright. The archived state carries over between records in the
        same batch, so a dead model is only ever hit once per run.

        account is a sudo() recordset (see action_generate): the AI Agent
        account/token/models are admin-only data (Settings > AI Agent,
        restricted to base.group_system), but any user allowed to run this
        wizard must still be able to use them to generate a report."""
        model = account.default_model_id
        tried_ids = []
        while model:
            try:
                return generate_text(account.provider, account.api_token, model.model_code, prompt)
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

        self.result_ids.unlink()
        for record in records:
            prompt = self._build_prompt(record)
            text = self._generate_with_fallback(account, prompt)
            self.env['ai.report.agent.wizard.line'].create({
                'wizard_id': self.id,
                'res_model': record._name,
                'res_id': record.id,
                'record_display_name': record.display_name,
                'generated_text': text,
            })

        self.state = 'preview'
        return {
            'name': _("Report Preview"),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.report.agent.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print(self):
        self.ensure_one()
        return self.env.ref('omnia_report_ai_agent.action_report_ai_agent').report_action(self)


class AiReportAgentWizardLine(models.TransientModel):
    _name = 'ai.report.agent.wizard.line'
    _description = 'AI Report Agent Wizard Result'

    wizard_id = fields.Many2one('ai.report.agent.wizard', required=True, ondelete='cascade')
    res_model = fields.Char()
    res_id = fields.Integer()
    record_display_name = fields.Char()
    generated_text = fields.Text()
