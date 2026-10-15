"""Conservative literal coverage for text-only support review, not a truth judge.

Derived or spelled-out values need separate validation; they are never converted
into invented evidence here. Visual claims remain the vision reviewer's job.
"""
import re
from decimal import Decimal


def literals(text):
    text = re.sub(r'\[\d+\]', '', str(text)).lower()
    # Equivalent numeric date separators/order retain the same literal parts.
    # Do not strip zeroes from arbitrary identifiers.
    text = re.sub(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
                  lambda m: ' '.join(str(int(p)) for p in m.groups()), text)
    text = re.sub(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
                  lambda m: ' '.join(str(int(p)) for p in m.groups()), text)
    # Joined standard quantity/unit notation is prose, not a model identifier.
    text = re.sub(r'(?<!\w)(\d+(?:\.\d+)?)(kwh|kw|kg|mm|cm|bar|watts?|volts?|amps?|months?|years?|days?|hours?|minutes?|seconds?|w|v)\b',
                  r'\1 \2', text)
    result = set()
    def identifier(match):
        value = match.group()
        if any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
            # Allow only a simple letter-prefix separator; arbitrary internal
            # separators can distinguish real model/serial identifiers.
            value = re.sub(r'^([a-z]+)[-/.](\d+[a-z]*)$', r'\1\2', value)
            result.add('id:' + value)
            return ' '
        return value
    text = re.sub(r'\b[a-z0-9]+(?:[-/.][a-z0-9]+)*\b', identifier, text)
    def digit_identifier(match):
        result.add('digits:' + re.sub(r'\D', '', match.group()))
        return ' '
    # Preserve long identifier zeroes and allow common grouped-card formatting.
    text = re.sub(r'(?<!\w)(?:\d{8,}|\d{3,4}(?:[ -]\d{3,4}){2,})(?!\w)', digit_identifier, text)
    for match in re.finditer(r'(?<![\w])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?![\w])', text):
        value = match.group().replace(',', '')
        if '.' not in value and len(value.lstrip('+-')) > 1 and value.lstrip('+-').startswith('0'):
            result.add('number:' + value.lstrip('+'))
        else:
            result.add('number:' + str(Decimal(value).normalize()))
    return result


def supported_literals(section, evidence, question=''):
    from .vision_assets import needs_image
    # Headings are rendered as answer prose too. Invalid non-string fields must
    # fail closed instead of bypassing checks through implicit coercion.
    heading, body = section.get('heading', ''), section.get('text', '')
    if not isinstance(heading, str) or not isinstance(body, str):
        return False
    cited = [row for row in evidence if row.get('index') in section.get('evidence', [])]
    if not cited:
        return False
    # A chart/OCR image can legitimately supply numbers missing from its title.
    if any(row.get('image_path') and needs_image([row], question) for row in cited):
        return True
    supported = set().union(*(literals(row.get('text', '')) for row in cited))
    return literals(heading + '\n' + body).issubset(supported)
