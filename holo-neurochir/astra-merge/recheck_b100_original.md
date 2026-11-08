# Mechanical behavioral audit

PASS: raw counts were recomputed and matched the supplied summary and frozen cohort.

- Rows: 51 (48 structured + 3 text)
- Errors: 0; truncated: 6
- fs+: {'answer': 2, 'valid_nonanswer': 7, 'invalid': 7}
- fs-: {'answer': 5, 'valid_nonanswer': 2, 'invalid': 9}
- healthy: {'answer': 0, 'valid_nonanswer': 16, 'invalid': 0}

Invalid mechanism counts are computed from raw `tool`/`finish_reason`/`truncated` fields:

- fs+: {'stop:empty_or_unparsed': 7}
- fs-: {'stop:empty_or_unparsed': 3, 'length:truncated': 6}

Text transport: {'nonempty': 3, 'stop': 3}
