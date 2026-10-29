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
import time

import requests

DEFAULT_TIMEOUT = 15
GENERATE_TIMEOUT = 60
MAX_TOKENS = 4096
MAX_RETRIES = 2
RETRY_DELAY = 2


class AiProviderAuthError(Exception):
    """The API token is missing or was rejected by the provider."""


class AiProviderApiError(Exception):
    """The API call failed for any other reason (network, bad request, ...)."""


class AiProviderModelUnavailableError(AiProviderApiError):
    """The specific model is gone/retired for this account -- raised when a
    generation call itself 404s, not when fetching the model list."""


def _request(provider_label, method, url, **kwargs):
    """requests.get/post wrapper shared by every provider call, retrying
    only a timeout/dropped connection (never an actual 4xx/5xx response)
    up to MAX_RETRIES times before raising AiProviderApiError."""
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return method(url, **kwargs)
        except requests.exceptions.Timeout as exc:
            last_exc = exc
        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    if isinstance(last_exc, requests.exceptions.Timeout):
        raise AiProviderApiError(
            "%s's API took too long to respond (tried %d times). This can happen with long "
            "instructions or large attachments -- try again, or shorten the request."
            % (provider_label, MAX_RETRIES + 1)
        ) from last_exc
    raise AiProviderApiError(
        "Could not reach %s's API after %d attempts: %s" % (provider_label, MAX_RETRIES + 1, last_exc)
    ) from last_exc


def _list_models_anthropic(api_key):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "Claude", requests.get,
        "https://api.anthropic.com/v1/models",
        headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01'},
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("Claude rejected this API token.")
    if not response.ok:
        raise AiProviderApiError(
            "Claude's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    return [
        {'code': item['id'], 'name': item.get('display_name') or item['id']}
        for item in response.json().get('data', [])
    ]


def _list_models_openai(api_key):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "OpenAI", requests.get,
        "https://api.openai.com/v1/models",
        headers={'Authorization': 'Bearer %s' % api_key},
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("OpenAI rejected this API token.")
    if not response.ok:
        raise AiProviderApiError(
            "OpenAI's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    return [{'code': item['id'], 'name': item['id']} for item in response.json().get('data', [])]


def _list_models_google(api_key):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "Gemini", requests.get,
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={'key': api_key},
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code in (401, 403):
        raise AiProviderAuthError("Gemini rejected this API token.")
    if not response.ok:
        raise AiProviderApiError(
            "Gemini's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    models = []
    for item in response.json().get('models', []):
        if 'generateContent' not in item.get('supportedGenerationMethods', []):
            continue
        code = (item.get('name') or '').split('/')[-1]
        if code:
            models.append({'code': code, 'name': item.get('displayName') or code})
    return models


def _list_models_groq(api_key):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "Groq", requests.get,
        "https://api.groq.com/openai/v1/models",
        headers={'Authorization': 'Bearer %s' % api_key},
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("Groq rejected this API token.")
    if not response.ok:
        raise AiProviderApiError(
            "Groq's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    return [{'code': item['id'], 'name': item['id']} for item in response.json().get('data', [])]


_LIST_MODELS = {
    'anthropic': _list_models_anthropic,
    'openai': _list_models_openai,
    'google': _list_models_google,
    'groq': _list_models_groq,
}


def list_models(provider, api_key):
    """Return [{'code': ..., 'name': ...}, ...] for the given provider, or
    raise AiProviderAuthError / AiProviderApiError."""
    try:
        func = _LIST_MODELS[provider]
    except KeyError:
        raise ValueError("Unknown AI provider: %s" % provider) from None
    return func(api_key)


def _generate_text_anthropic(api_key, model, prompt, images=None):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    content = prompt
    if images:
        content = [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': img['mimetype'], 'data': img['data_base64']}}
            for img in images
        ] + [{'type': 'text', 'text': prompt}]
    response = _request(
        "Claude", requests.post,
        "https://api.anthropic.com/v1/messages",
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': model,
            'max_tokens': MAX_TOKENS,
            'messages': [{'role': 'user', 'content': content}],
        },
        timeout=GENERATE_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("Claude rejected this API token.")
    if response.status_code == 404:
        raise AiProviderModelUnavailableError("Model '%s' is not available." % model)
    if not response.ok:
        raise AiProviderApiError(
            "Claude's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    data = response.json()
    return "".join(part.get('text', '') for part in data.get('content', []))


def _generate_text_openai(api_key, model, prompt, images=None):
    # images is accepted for a uniform call signature across providers but
    # unused here -- not every fetched model is vision-capable and we have
    # no way to tell which is, so this provider stays text-only for now.
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "OpenAI", requests.post,
        "https://api.openai.com/v1/chat/completions",
        headers={'Authorization': 'Bearer %s' % api_key, 'content-type': 'application/json'},
        json={
            'model': model,
            'max_tokens': MAX_TOKENS,
            'messages': [{'role': 'user', 'content': prompt}],
        },
        timeout=GENERATE_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("OpenAI rejected this API token.")
    if response.status_code == 404:
        raise AiProviderModelUnavailableError("Model '%s' is not available." % model)
    if not response.ok:
        raise AiProviderApiError(
            "OpenAI's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    data = response.json()
    return data['choices'][0]['message']['content']


def _generate_text_google(api_key, model, prompt, images=None):
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    parts = [{'inline_data': {'mime_type': img['mimetype'], 'data': img['data_base64']}} for img in (images or [])]
    parts.append({'text': prompt})
    response = _request(
        "Gemini", requests.post,
        "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model,
        params={'key': api_key},
        json={'contents': [{'parts': parts}]},
        timeout=GENERATE_TIMEOUT,
    )
    if response.status_code in (401, 403):
        raise AiProviderAuthError("Gemini rejected this API token.")
    if response.status_code == 404:
        raise AiProviderModelUnavailableError("Model '%s' is not available." % model)
    if not response.ok:
        raise AiProviderApiError(
            "Gemini's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    data = response.json()
    parts = data['candidates'][0]['content']['parts']
    return "".join(part.get('text', '') for part in parts)


def _generate_text_groq(api_key, model, prompt, images=None):
    # images accepted for a uniform signature, unused -- most Groq-hosted
    # models have no reliable image support.
    if not api_key:
        raise AiProviderAuthError("No API token configured.")
    response = _request(
        "Groq", requests.post,
        "https://api.groq.com/openai/v1/chat/completions",
        headers={'Authorization': 'Bearer %s' % api_key, 'content-type': 'application/json'},
        json={
            'model': model,
            'max_tokens': MAX_TOKENS,
            'messages': [{'role': 'user', 'content': prompt}],
        },
        timeout=GENERATE_TIMEOUT,
    )
    if response.status_code == 401:
        raise AiProviderAuthError("Groq rejected this API token.")
    if response.status_code == 404:
        raise AiProviderModelUnavailableError("Model '%s' is not available." % model)
    if not response.ok:
        raise AiProviderApiError(
            "Groq's API returned an error (%s): %s" % (response.status_code, response.text[:300])
        )
    data = response.json()
    return data['choices'][0]['message']['content']


_GENERATE_TEXT = {
    'anthropic': _generate_text_anthropic,
    'openai': _generate_text_openai,
    'google': _generate_text_google,
    'groq': _generate_text_groq,
}


def generate_text(provider, api_key, model, prompt, images=None):
    """Send prompt (and images, if this provider supports them -- Claude
    and Gemini today) to the given provider/model, returning its plain-text
    answer or raising AiProviderAuthError / AiProviderApiError."""
    try:
        func = _GENERATE_TEXT[provider]
    except KeyError:
        raise ValueError("Unknown AI provider: %s" % provider) from None
    return func(api_key, model, prompt, images=images)
