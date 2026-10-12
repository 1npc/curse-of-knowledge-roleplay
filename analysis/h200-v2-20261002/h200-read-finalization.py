"""Read the original finalizer's outcome without restarting any process."""
from pathlib import Path
import datetime
import hashlib
import json

root = Path('/data/qianru/over-comprehension-v2-20261001')
receipt = root / 'operations/campaign-finalized.json'
report = root / 'analysis/results.json'
result = {'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'finalized': receipt.is_file()}
if receipt.is_file():
    result['receipt'] = json.loads(receipt.read_text())
    result['report_sha256'] = hashlib.sha256(report.read_bytes()).hexdigest()
    result['report'] = json.loads(report.read_text())
print(json.dumps(result))
