# Lab 01 - Resource governance, RBAC and policy

Run the commands from the folder containing `azlocal.py`.

```bash
python3 azlocal.py init
python3 azlocal.py group create rg-icdfa-lab --owner Student --environment training
python3 azlocal.py group list
python3 azlocal.py access assign analyst Reader group:rg-icdfa-lab
python3 azlocal.py access check analyst write group:rg-icdfa-lab
python3 azlocal.py --actor analyst vm create denied-demo --group rg-icdfa-lab
python3 azlocal.py group lock rg-icdfa-lab
python3 azlocal.py policy
python3 azlocal.py group unlock rg-icdfa-lab
```

The denied VM create command should exit with an RBAC error. Do not mistake the denial for a lab failure.

Tasks: explain Owner vs Reader, capture the deny event, explain tags, resource scopes and locks. Name one respect in which this simulator differs from Microsoft Entra ID and Azure RBAC.

Evidence: screenshots/output, RBAC table, short governance finding.
