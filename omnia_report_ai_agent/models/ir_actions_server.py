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

from lxml import etree

from odoo import _, fields, models
from odoo.exceptions import UserError

from .ai_agent_field_utils import (
    get_ownership_caution_note, get_record_context, is_reportable_field, is_skipped_field,
)
from .ai_agent_provider_client import AiProviderApiError, AiProviderAuthError, generate_text


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
    ai_agent_report_structure = fields.Text(
        string="AI Report Structure",
        readonly=True,
        help="The QWeb markup the AI designed for the generated Print report "
             "below. Technical/internal -- redo it with \"Generate Template "
             "with AI\" rather than editing this directly.",
    )
    ai_agent_report_action_id = fields.Many2one(
        'ir.actions.report',
        string="Generated Print Report",
        readonly=True,
        help="The normal report created from the structure above. Shows up "
             "under this model's own Print menu, named so it's recognizable "
             "there. Re-running \"Generate Template with AI\" updates it in "
             "place rather than duplicating it.",
    )

    def _get_ai_agent_template_view(self):
        """The ir.ui.view action_generate_ai_template created/updated for
        this action, found by the same deterministic key it always uses."""
        self.ensure_one()
        if not isinstance(self.id, int):
            return self.env['ir.ui.view']
        key = 'omnia_report_ai_agent.ai_template_%d' % self.id
        return self.env['ir.ui.view'].sudo().search([('key', '=', key)], limit=1)

    def _run_action_ai_agent_report_multi(self, eval_context=None):
        """Run the AI Report Agent on this action's record(s) using its
        predefined Command/Instructions, then open the Preview."""
        self.ensure_one()
        active_model = self._context.get('active_model') or self.model_name
        active_ids = self._context.get('active_ids')
        if not active_ids and self._context.get('active_id'):
            active_ids = [self._context['active_id']]
        wizard = self.env['ai.report.agent.wizard'].create({
            'res_model': active_model,
            'res_ids': ",".join(str(i) for i in (active_ids or [])),
            'server_action_id': self.id,
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

    def _describe_model_for_template_design(self, model_name):
        """List this model's own fields and relations (names, types, labels
        only -- no record data, this designs a layout for every record of
        the model, not one specific one) for the AI."""
        Model = self.env[model_name]
        lines = ["Plain fields available on %s:" % model_name]
        for fname, field in Model._fields.items():
            if is_skipped_field(fname) or not is_reportable_field(field):
                continue
            lines.append("- %s (%s): %s" % (fname, field.type, field.string))

        lines.append("")
        lines.append("One2many/Many2many relations available on %s:" % model_name)
        for fname, field in Model._fields.items():
            if field.type not in ('one2many', 'many2many') or is_skipped_field(fname):
                continue
            Comodel = self.env[field.comodel_name]
            lines.append("- %s -> %s: %s" % (fname, field.comodel_name, field.string))
            note = get_ownership_caution_note(field, self.env)
            if note:
                lines.append("    NOTE: %s." % note)
            for cfname, cfield in Comodel._fields.items():
                if is_skipped_field(cfname) or not is_reportable_field(cfield):
                    continue
                lines.append("    - %s (%s): %s" % (cfname, cfield.type, cfield.string))
        return "\n".join(lines)

    def _build_template_design_prompt(self, model_name):
        self.ensure_one()
        parts = [
            "You are writing the actual QWeb report template body for every "
            "\"%s\" record -- not a plan, the real markup, and not one "
            "specific record's data, a reusable layout. Return ONLY the "
            "inner QWeb/HTML fragment (no markdown, no code fences, no "
            "commentary) -- no <?xml?> declaration, and no outer <t t-name>/"
            "<t t-call=\"web.html_container\">/<t t-call=\"web.external_layout\">/"
            "<div class=\"page\"> wrapper, we add all of that ourselves. "
            "Design the whole thing yourself: headings, tables, which "
            "fields to show and how -- whatever best fits the Task/"
            "Instructions below. A clean, consistent table style (borders, "
            "bold header row) matching Odoo's own native report look is "
            "already applied automatically to everything you write -- do "
            "not add your own <style> block or invent colors/fonts, just "
            "write plain table/heading markup and it will already look "
            "consistent with every other Odoo report." % model_name,
            "Allowed tags: div, table, thead, tbody, tr, td, th, h1-h6, p, "
            "ul, ol, li, strong, b, em, i, span, small, br, hr, and QWeb's "
            "own t (for t-foreach/t-if/t-call). Allowed plain attributes: "
            "class, style, colspan, rowspan. No other tags (no script/img/"
            "a/iframe/style/etc.) or attributes.",
            "Every t-field/t-esc/t-out/t-foreach value must be a real, "
            "dotted field path starting with \"doc\" (doc.<field>, or "
            "doc.<field>.<field_of_that_relation>, as many hops as needed). "
            "A t-foreach's value must be a one2many/many2many field path, "
            "paired with a t-as naming a loop variable -- fields are then "
            "read off that variable the same way (<loop_var>.<field>). "
            "Every single hop in any path must be a real field of whatever "
            "model it's on at that point -- you decide which fields exist "
            "and which are relevant purely from the schema below (and, for "
            "a relation, by chaining into that relation's own model using "
            "your own knowledge of Odoo's standard models) -- we check each "
            "hop against the real field registry, not against examples, so "
            "there's no fixed list of \"correct\" fields to match, only "
            "whether what you wrote is real. Nothing else is allowed in "
            "t-field/t-esc/t-out/t-foreach -- no method calls, no "
            "arithmetic, no string formatting.",
            "t-if/t-elif ARE allowed, conditioned on real fields, in any "
            "of these shapes: a bare field path (truthy check), a negated "
            "one (\"not \" + field path), a field path compared to a "
            "literal with ==, !=, &gt;, &lt;, &gt;=, or &lt;=, or a field "
            "path's membership in a literal list with \"in\"/\"not in\". "
            "The field path side follows the same real-field-path rules as "
            "t-field above -- again, decided from the schema, not from an "
            "example; the other side must be a plain literal (a quoted "
            "string, a number, or True/False/None) -- never another field "
            "path, method call, or arithmetic.",
            "A record of this model may have no data for some of the "
            "sections you design -- an empty one2many relation, or a plain "
            "field with no value. Never show a table with a heading and "
            "column headers but zero rows, and never show a field's label "
            "with nothing next to it -- both look broken, not just empty. "
            "Wrap each such section in a t-if on that same field/relation "
            "(e.g. t-if=\"doc.<field>\" around the heading AND the table or "
            "row together, not just the table) so the whole section is "
            "skipped for a record that has nothing there.",
        ]
        if self.ai_agent_command:
            parts.append("Task: %s" % self.ai_agent_command)
        if self.ai_agent_instructions:
            parts.append("Instructions: %s" % self.ai_agent_instructions)
        parts.append(self._describe_model_for_template_design(model_name))
        sample_record = self.env[model_name].search([], limit=1)
        sample_context = get_record_context(sample_record) if sample_record else ""
        if sample_context:
            parts.append(
                "Example record (for context only -- design a layout that "
                "works for EVERY record of this model, not just this one):"
                "\n%s" % sample_context
            )
        return "\n\n".join(parts)

    _ALLOWED_TAGS = {
        't', 'div', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li',
        'strong', 'b', 'em', 'i', 'span', 'small', 'br', 'hr',
    }
    _ALLOWED_PLAIN_ATTRS = {'class', 'style', 'colspan', 'rowspan'}
    _ALLOWED_T_CALL_TARGETS = {'account.document_tax_totals'}
    _UNSAFE_STYLE_RE = re.compile(r'url\s*\(|expression\s*\(|javascript:', re.IGNORECASE)
    _FIELD_PATH_RE = re.compile(
        r'^(?P<base>[A-Za-z_][A-Za-z0-9_]*)'
        r'(?P<path>(?:\.[A-Za-z_][A-Za-z0-9_]*)*)'
        r'(?:\.filtered\(lambda\s+(?P<lvar>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*not\s+(?P=lvar)\.display_type\))?$'
    )
    _LITERAL = r"'[^'\\]*'|\"[^\"\\]*\"|-?\d+(?:\.\d+)?|True|False|None"
    _COND_CMP_RE = re.compile(
        r'^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s*(?P<op><=|>=|==|!=|<|>)\s*'
        r'(?P<literal>%s)$' % _LITERAL
    )
    _COND_IN_RE = re.compile(
        r'^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s+(?P<neg>not\s+)?in\s*'
        r'\((?P<items>(?:\s*(?:%s)\s*,?)+)\)$' % _LITERAL
    )

    def _resolve_field_path(self, expr, scope, mode):
        """Validate one field-path expression against scope (variable name
        -> real model held) by walking every dotted hop against the field
        registry."""
        match = self._FIELD_PATH_RE.match(expr)
        if not match:
            raise UserError(_(
                "The AI used \"%s\", which isn't a plain field path. Try "
                "generating the template again."
            ) % expr)
        base = match.group('base')
        if base not in scope:
            raise UserError(_(
                "The AI referenced \"%s\", which isn't a known record "
                "variable at that point. Try generating the template again."
            ) % base)
        current_model_name = scope[base]
        field = None
        for seg in [s for s in (match.group('path') or '').split('.') if s]:
            Model = self.env.get(current_model_name) if current_model_name else None
            if Model is None or seg not in Model._fields:
                raise UserError(_(
                    "The AI referenced \"%s\" on %s, which isn't a real "
                    "field. Try generating the template again."
                ) % (seg, current_model_name or expr))
            field = Model._fields[seg]
            if field.type == 'one2many':
                note = get_ownership_caution_note(field, self.env)
                if note:
                    raise UserError(_(
                        "The AI used \"%s\", but %s -- not allowed in a "
                        "generated report template. Try generating the "
                        "template again."
                    ) % (seg, note))
            current_model_name = field.comodel_name if field.relational else None
        if match.group('lvar'):
            Model = self.env.get(current_model_name) if current_model_name else None
            if Model is None or 'display_type' not in Model._fields:
                raise UserError(_(
                    "The AI used a .filtered(...) clause on %s, which has "
                    "no display_type field. Try generating the template "
                    "again."
                ) % (current_model_name or expr))
        if mode == 'foreach':
            if not field or field.type not in ('one2many', 'many2many'):
                raise UserError(_(
                    "The AI used \"%s\" in a t-foreach, but that isn't a "
                    "one2many/many2many field. Try generating the template "
                    "again."
                ) % expr)
        elif mode == 'leaf' and field and field.type in ('one2many', 'many2many'):
            raise UserError(_(
                "The AI used \"%s\" as a plain value, but that's a "
                "one2many/many2many field (needs a t-foreach, not a "
                "t-field/t-esc). Try generating the template again."
            ) % expr)
        return current_model_name

    def _validate_condition_expr(self, expr, scope):
        """Validate one t-if/t-elif expression against _COND_CMP_RE/
        _COND_IN_RE, resolving its field-path side via _resolve_field_path."""
        for regex in (self._COND_IN_RE, self._COND_CMP_RE):
            match = regex.match(expr)
            if match:
                self._resolve_field_path(match.group('path'), scope, mode='condition')
                return
        path = expr[4:].strip() if expr.startswith('not ') else expr
        if self._FIELD_PATH_RE.match(path):
            self._resolve_field_path(path, scope, mode='condition')
            return
        raise UserError(_(
            "The AI used a condition (\"%s\") that isn't a plain field "
            "check. Try generating the template again."
        ) % expr)

    def _check_ai_template_node(self, el, scope):
        """Recursively validate one element (and its attributes, then its
        children) of the AI's returned template -- see
        _validate_ai_template_body."""
        if not isinstance(el.tag, str):
            return
        tag = etree.QName(el).localname
        if tag not in self._ALLOWED_TAGS:
            raise UserError(_(
                "The AI used a <%s> tag, which isn't allowed in a generated "
                "report template. Try generating the template again."
            ) % tag)
        child_scope = scope
        for attr, value in el.attrib.items():
            if attr in self._ALLOWED_PLAIN_ATTRS:
                if attr == 'style' and self._UNSAFE_STYLE_RE.search(value):
                    raise UserError(_(
                        "The AI's styling used a disallowed pattern. Try "
                        "generating the template again."
                    ))
                continue
            if attr == 't-call':
                if value not in self._ALLOWED_T_CALL_TARGETS:
                    raise UserError(_(
                        "The AI tried to call \"%s\", which isn't an "
                        "allowed template. Try generating the template "
                        "again."
                    ) % value)
                continue
            if attr == 't-set':
                if value not in ('tax_totals', 'currency'):
                    raise UserError(_(
                        "The AI used an unexpected t-set (\"%s\"). Try "
                        "generating the template again."
                    ) % value)
                continue
            if attr == 't-value':
                if value not in ('doc.tax_totals', 'doc.currency_id'):
                    raise UserError(_(
                        "The AI used an unexpected t-value (\"%s\"). Try "
                        "generating the template again."
                    ) % value)
                continue
            if attr in ('t-if', 't-elif'):
                self._validate_condition_expr(value, scope)
                continue
            if attr == 't-else':
                continue
            if attr == 't-as':
                continue
            if attr in ('t-field', 't-esc', 't-out'):
                self._resolve_field_path(value, scope, mode='leaf')
                continue
            if attr == 't-foreach':
                loop_model = self._resolve_field_path(value, scope, mode='foreach')
                t_as = el.get('t-as')
                if not t_as:
                    raise UserError(_(
                        "The AI used t-foreach=\"%s\" without a t-as. Try "
                        "generating the template again."
                    ) % value)
                child_scope = dict(scope)
                child_scope[t_as] = loop_model
                continue
            raise UserError(_(
                "The AI used an attribute (\"%s\") that isn't allowed in a "
                "generated report template. Try generating the template "
                "again."
            ) % attr)
        for child in el:
            self._check_ai_template_node(child, child_scope)

    def _validate_ai_template_body(self, raw_text, model_name):
        """Parse and strictly validate the AI's own QWeb markup before it's
        ever saved as a permanent, reusable report template."""
        text = self._strip_code_fence(raw_text)
        try:
            root = etree.fromstring('<ai-root>%s</ai-root>' % text)
        except etree.XMLSyntaxError as exc:
            raise UserError(_(
                "The AI didn't return well-formed markup (%s). Try "
                "generating the template again."
            ) % exc)
        for child in root:
            self._check_ai_template_node(child, {'doc': model_name})
        serialized = etree.tostring(root, encoding='unicode')
        return serialized[len('<ai-root>'):-len('</ai-root>')]

    @staticmethod
    def _strip_code_fence(text):
        text = (text or '').strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]
            if text.endswith('```'):
                text = text.rsplit('```', 1)[0]
        return text.strip()

    def action_generate_ai_template(self):
        """One-time AI-assisted design of a normal Print-menu report for
        this action's model, independent of the per-print free-text flow."""
        self.ensure_one()
        if self.state != 'ai_agent_report':
            raise UserError(_("This is only available for an \"AI Agent Report\" action."))
        if not self.model_id:
            raise UserError(_("Set a Model on this action first."))

        account = self.env['ai.agent.provider.account'].sudo()._get_default_account()
        if not account or not account.api_token:
            raise UserError(_("Set up the AI Agent in Settings > AI Agent first."))
        if not account.default_model_id:
            raise UserError(_(
                "Pick a Default Model in Settings > AI Agent (click \"Fetch Models\" if the "
                "list is still empty) before generating a template."
            ))

        model_name = self.model_id.model
        prompt = self._build_template_design_prompt(model_name)
        try:
            raw = generate_text(account.provider, account.api_token, account.default_model_id.model_code, prompt)
        except (AiProviderAuthError, AiProviderApiError) as exc:
            raise UserError(str(exc)) from exc

        body = self._validate_ai_template_body(raw, model_name)
        self.ai_agent_report_structure = body

        key = 'omnia_report_ai_agent.ai_template_%d' % self.id
        arch = (
            '<t t-name="%s">\n'
            '<t t-call="web.html_container">\n'
            '<t t-foreach="docs" t-as="doc">\n'
            '<t t-call="web.external_layout">\n'
            '<div class="page">\n'
            '<style>\n'
            '  .ai_agent_report_body table { border-collapse: collapse; width: 100%%; table-layout: fixed; margin-bottom: 16px; font-size: 10px; }\n'
            '  .ai_agent_report_body th, .ai_agent_report_body td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; word-wrap: break-word; overflow-wrap: break-word; }\n'
            '  .ai_agent_report_body th { background-color: #f5f5f5; font-weight: bold; }\n'
            '  .ai_agent_report_body h1, .ai_agent_report_body h2, .ai_agent_report_body h3 { border-bottom: 1px solid #dee2e6; padding-bottom: 4px; margin-top: 16px; }\n'
            '  .ai_agent_report_body thead { display: table-header-group; }\n'
            '  .ai_agent_report_body tr { page-break-inside: avoid; }\n'
            '  .ai_agent_report_body h1, .ai_agent_report_body h2, .ai_agent_report_body h3,\n'
            '  .ai_agent_report_body h4, .ai_agent_report_body h5, .ai_agent_report_body h6 { page-break-after: avoid; }\n'
            '</style>\n'
            '<div class="ai_agent_report_body">%s</div>\n'
            '</div>\n'
            '</t></t></t></t>'
        ) % (key, body)

        view = self._get_ai_agent_template_view()
        view_vals = {
            'name': "%s - AI Report Template (%s)" % (
                self.name or _("AI Report"), key.split('.', 1)[1],
            ),
            'type': 'qweb',
            'arch': arch,
            'key': key,
        }
        if view:
            view.write(view_vals)
        else:
            view = self.env['ir.ui.view'].sudo().create(view_vals)

        report_vals = {
            'name': self.name or _("AI Report"),
            'model': model_name,
            'report_type': 'qweb-pdf',
            'report_name': key,
            'report_file': key,
            'paperformat_id': self.env.company.paperformat_id.id,
            'binding_model_id': self.model_id.id,
            'binding_type': 'report',
            'print_report_name': "%r + ' - ' + (object.display_name or '')" % (self.name or 'AI Report'),
        }
        if self.ai_agent_report_action_id:
            self.ai_agent_report_action_id.sudo().write(report_vals)
        else:
            report = self.env['ir.actions.report'].sudo().create(report_vals)
            self.ai_agent_report_action_id = report.id

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Template generated successfully"),
                'message': self.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
