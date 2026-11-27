# Lab 03 - Storage access, file integrity and backup/recovery

```bash
python3 azlocal.py storage create sticdfalab --group rg-icdfa-lab
python3 azlocal.py storage set sticdfalab --public-access true --https-only false
python3 azlocal.py policy
python3 azlocal.py storage set sticdfalab --public-access false --https-only true
python3 azlocal.py blob upload sticdfalab operations-file --file samples/operations_data.txt
python3 azlocal.py blob verify sticdfalab operations-file
python3 azlocal.py backup create known-good
python3 azlocal.py vm stop vm-demo
python3 azlocal.py backup restore known-good --confirm
python3 azlocal.py vm list
```

Tasks: note simulated configuration findings and remediation, verify SHA-256, perform inventory rollback, distinguish inventory backup from full file or VM disk backup.

Important: the backup only snapshots the simulator's JSON inventory. It does not restore Azure data, real virtual machine disks or local blob bytes.

Evidence: policy comparison, blob SHA-256, backup record, VM state before/after.
