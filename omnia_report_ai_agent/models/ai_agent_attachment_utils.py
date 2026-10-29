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
import base64
import io

MAX_TEXT_CHARS_PER_FILE = 5000
MAX_IMAGES = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024

TEXT_MIMETYPE_PREFIX = 'text/'
PDF_MIMETYPE = 'application/pdf'
IMAGE_MIMETYPE_PREFIX = 'image/'


def _extract_pdf_text(raw_bytes):
    """Plain text from a text-based PDF via PyPDF2 (already an Odoo
    dependency, nothing new to install) -- None for a scanned/image-only
    PDF or anything PyPDF2 can't parse (no OCR)."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        return "\n".join((page.extract_text() or '') for page in reader.pages)
    except Exception:
        return None


def describe_attachments(attachments):
    """(text_context, images) for the given ir.attachment recordset.

    text_context: one block of text per readable attachment (.txt/.csv
    decoded directly, PDF via _extract_pdf_text), each capped at
    MAX_TEXT_CHARS_PER_FILE and marked if truncated, ready to append to an
    AI prompt as-is -- plain text works identically for every provider.
    Anything else (images, Word/Excel, a scanned PDF) gets a one-line note
    by filename instead of silently vanishing, since it genuinely wasn't
    read.

    images: up to MAX_IMAGES entries (capped by MAX_IMAGE_BYTES combined),
    each {'mimetype': ..., 'data_base64': ..., 'name': ...} -- the caller
    decides whether the chosen provider actually supports sending these
    (today: Claude and Gemini only; see ai_agent_provider_client.py).
    """
    text_lines = []
    images = []
    image_bytes_total = 0
    for attachment in attachments:
        raw = attachment.raw or b''
        mimetype = attachment.mimetype or ''
        if mimetype.startswith(IMAGE_MIMETYPE_PREFIX):
            if len(images) >= MAX_IMAGES or image_bytes_total + len(raw) > MAX_IMAGE_BYTES:
                text_lines.append(
                    "Attachment '%s' is an image but was skipped (too many or too large "
                    "image attachments already included)." % attachment.name
                )
                continue
            images.append({
                'mimetype': mimetype,
                'data_base64': base64.b64encode(raw).decode('ascii'),
                'name': attachment.name,
            })
            image_bytes_total += len(raw)
            continue

        text = None
        if mimetype.startswith(TEXT_MIMETYPE_PREFIX):
            try:
                text = raw.decode('utf-8', errors='replace')
            except Exception:
                text = None
        elif mimetype == PDF_MIMETYPE:
            text = _extract_pdf_text(raw)

        if text is None:
            text_lines.append(
                "Attachment '%s' (%s) could not be read as text, skipped."
                % (attachment.name, mimetype or "unknown type")
            )
            continue
        text = text.strip()
        if not text:
            continue
        truncated = len(text) > MAX_TEXT_CHARS_PER_FILE
        text_lines.append(
            "Attachment '%s' content%s:\n%s"
            % (attachment.name, " (truncated)" if truncated else "", text[:MAX_TEXT_CHARS_PER_FILE])
        )

    return "\n\n".join(text_lines), images
