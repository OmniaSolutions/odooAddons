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

SKIP_FIELD_NAMES = {'id', 'display_name', '__last_update', 'create_date', 'write_date', 'create_uid', 'write_uid'}
SKIP_FIELD_PREFIXES = ('message_', 'activity_', 'access_', 'website_')


def is_reportable_field(field):
    """True for a plain, displayable field: not binary/html/a collection,
    and not an unstored compute (nothing to read back)."""
    if field.type in ('binary', 'one2many', 'many2many', 'html'):
        return False
    if field.compute and not field.store:
        return False
    return True


def is_skipped_field(name):
    return name in SKIP_FIELD_NAMES or name.startswith(SKIP_FIELD_PREFIXES)


def get_ownership_caution_note(field, env):
    """None if this one2many's rows are genuinely owned by the record;
    otherwise a generic caution, computed from Odoo's own ondelete
    metadata -- same logic for every one2many on every model."""
    if field.type != 'one2many' or not field.inverse_name:
        return None
    try:
        inverse_field = env[field.comodel_name]._fields.get(field.inverse_name)
    except Exception:
        return None
    if not inverse_field or inverse_field.type != 'many2one':
        return None
    if getattr(inverse_field, 'ondelete', None) == 'cascade':
        return None
    return (
        "these rows are not deleted along with this record (they have "
        "their own lifecycle and merely reference it) -- they may belong "
        "to or be about some OTHER record instead of being part of this "
        "one. Check what each row actually refers to before assuming this "
        "is this record's own data"
    )


def describe_record_fields(record, inline=False):
    """One line per plain (non-binary, non-x2many) field with a value."""
    parts = []
    for fname, field in record._fields.items():
        if is_skipped_field(fname) or not is_reportable_field(field):
            continue
        try:
            value = record[fname]
        except Exception:
            continue
        if value is False or value is None or value == '':
            continue
        if field.type == 'many2one':
            value = value.display_name
        parts.append("%s=%s" % (field.string, value) if inline else "- %s: %s" % (field.string, value))
    return parts


def _describe_nested_relations(sub, env, indent):
    """One extra hop of one2many relations nested under a one2many's own
    sub-record (e.g. a BoM's own component lines) -- a one2many's rows can
    themselves be a header with their own detail rows, invisible otherwise."""
    lines = []
    for fname, field in sub._fields.items():
        if field.type != 'one2many' or is_skipped_field(fname):
            continue
        try:
            nested = sub[fname]
        except Exception:
            continue
        if not nested:
            continue
        lines.append("%s%s (%s):" % (indent, field.string, fname))
        note = get_ownership_caution_note(field, env)
        if note:
            lines.append("%s  NOTE: %s." % (indent, note))
        for nested_sub in nested:
            parts = describe_record_fields(nested_sub, inline=True)
            if parts:
                lines.append("%s  - %s" % (indent, ", ".join(parts)))
    return lines


def get_record_context(record):
    if not record or not record.exists():
        return ""

    lines = ["Record: %s (%s, id %s)" % (record.display_name, record._name, record.id)]
    lines += describe_record_fields(record)

    for fname, field in record._fields.items():
        if field.type != 'one2many' or is_skipped_field(fname):
            continue
        try:
            sub_records = record[fname]
        except Exception:
            continue
        if not sub_records:
            continue
        lines.append("\n%s (%s):" % (field.string, fname))
        note = get_ownership_caution_note(field, record.env)
        if note:
            lines.append("  NOTE: %s." % note)
        for sub in sub_records:
            parts = describe_record_fields(sub, inline=True)
            if parts:
                lines.append("  - " + ", ".join(parts))
            if not note:
                lines += _describe_nested_relations(sub, record.env, "    ")

    return "\n".join(lines)
