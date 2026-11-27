# Lab 04 - Monitoring, alerts, audit trail and assurance reporting

```bash
python3 azlocal.py monitor rule high-cpu --threshold 85
python3 azlocal.py monitor sample
python3 azlocal.py monitor alerts
python3 azlocal.py monitor logs --limit 25
python3 azlocal.py policy
python3 azlocal.py report --output evidence/cloud_operations_report.json
sha256sum evidence/cloud_operations_report.json
```

Tasks: identify the resource and values that exceed threshold, inspect authorisation denials and security changes in the audit trail, produce a 5-entry risk register, create a change-control recommendation and an evidence-backed final report.

Metrics are synthetic. Logs of commands executed in the simulator are genuine local events, not Azure Monitor logs.

Evidence: alert output, audit excerpts, report JSON, SHA-256, risk register, final PDF.
