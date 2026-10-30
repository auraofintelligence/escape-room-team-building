"""Short source dates without turning inherited records into fresh verification."""
from datetime import date
def source_date(entry):
    value=entry.get('checked')
    if not value:return ''
    d=date.fromisoformat(value)
    short=f'{d.day} {d.strftime("%b %Y")}'
    if entry.get('verification_status')=='inherited_reference_requires_verification':return 'Unverified · Recorded '+short
    return 'Checked '+short
