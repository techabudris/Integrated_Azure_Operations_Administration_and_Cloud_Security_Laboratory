# Integrated_Azure_Operations_Administration_and_Cloud_Security_Laboratory

# CCSE-102 Offline Azure-Style Cloud Simulation & Security Audit

An offline Azure-style cloud governance, security hardening, integrity verification, backup/restore, and monitoring lab executed on **Kali Linux** (`~/Desktop/CCSE102_C1126CCSE17867_Lab/lab/lab`) using `azlocal.py` (`CCSE-102`, Student ID `C1126CCSE17867`). All operations run locally against simulated inventory records, local sample/backup files, and exported JSON evidence rather than a live Azure tenant[cite: 1, 2, 3, 21, 22].

---

## Overview & Scope

* **Simulation Engine:** Offline local simulator (`azlocal.py`) modeling resource group `rg-icdfa-lab`, network security group `nsg-demo`, storage account `sticdfalab`, blob storage (`operations-file`), virtual machine `vm-demo`, backup snapshots (`known-good`), CPU monitoring/alerts, audit logs, and signed JSON reporting (`evidence/cloud_operations_report.json`)[cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22].
* **Environment:** Kali Linux desktop session running from `~/Desktop/CCSE102_C1126CCSE17867_Lab/lab/lab` with workspace subdirectories (`evidence/`, `guides/`, `samples/`, `scripts/`, `templates/`, and `workspace/`)[cite: 1, 2, 3, 20, 21, 22].
* **Out of Scope:** Live Azure subscriptions, production workloads, real external network routing, and full cross-region disaster-recovery failover[cite: 1, 13, 15].

---

## Key Lab Findings

### Governance & RBAC (`rg-icdfa-lab`)
* Initialized the offline lab (`init`, `2026-11-23T19:12:19+00:00`) and created resource group `rg-icdfa-lab` (`group-create`, `2026-11-23T19:24:27+00:00`) under `student-admin`[cite: 11].
* Assigned `Reader` role on `group:rg-icdfa-lab` to `analyst` (`2026-11-23T19:26:38+00:00`), verified `write` was not permitted (`"permitted": false`, `2026-11-23T19:27:29+00:00`), and recorded a denied `write` authorization attempt (`"outcome": "denied"`, `2026-11-23T19:28:27+00:00`)[cite: 11, 12].
* Applied and later released a lock on `rg-icdfa-lab` (`group-lock` at `2026-11-23T19:32:04+00:00` and `group-unlock` at `2026-11-23T19:33:45+00:00`)[cite: 12, 13].

### Compute, NSG & Storage Hardening
* **VM Lifecycle (`vm-demo`):** Created `vm-demo` in `rg-icdfa-lab` (`"Ubuntu (simulated record)"`, size `"B1s"`, `2026-11-24T12:14:19+00:00`), started it (`2026-11-24T12:15:11+00:00`), stopped it (`"state": "stopped"`, `2026-11-24T13:20:43+00:00`), and restored it via `known-good` back to `"state": "running"`[cite: 3, 4, 5, 6, 10, 13, 16].
* **NSG Hardening (`nsg-demo`):** Removed the exposed `0.0.0.0/0` SSH port `22` rule at priority `200` (`nsg-remove`, `2026-11-24T12:34:41+00:00`) so access remained restricted to `192.168.56.0/24` (allowing `192.168.56.20` and denying `203.0.113.20`)[cite: 13, 14, 15].
* **Storage Hardening (`sticdfalab`):** Configured `"public_access": false` and `"https_only": true` on `sticdfalab` (`2026-11-24T12:58:54+00:00` and `2026-11-24T13:00:15+00:00`)[cite: 15].

### Integrity, Backup & Recovery Limitations
* **Blob Integrity:** Uploaded `samples/operations_data.txt` (`409` bytes) as `operations-file` to `sticdfalab` (`2026-11-24T13:11:19+00:00`) and verified `"integrity_ok": true` with SHA-256 `c067bc4c4808c9543f5c295cd5b41364b2705f7e2c6039394230589a1cf934f3`[cite: 1, 15].
* **Backup & Restore:** Created `known-good` backup (`checksum: 591b1e9d4628398167b528d98a394f0fe4f0a97e7d3fe8e5e4f093fc9b55f8ac`, saved to `workspace/backups/known-good.json`, `2026-11-24T13:20:08+00:00`) and restored it (`"verified": true`, `2026-11-24T13:21:39+00:00`)[cite: 2, 3, 5, 6, 10, 16].
* **Limitation:** Restoring `known-good` updates simulated inventory only (`"Inventory only; uploaded blob files are not reverted."`) and does not revert uploaded blob files or test live cross-region failover[cite: 1, 5, 6].

### Monitoring & Audit Trail
* Configured `"high-cpu"` rule (`"enabled": true`, `"metric": "cpu_percent"`, `"threshold": 85`) at `2026-11-25T09:08:51+00:00` and ingested `4` samples at `2026-11-25T09:09:32+00:00` (`32`, `86`, and `94` on `"vm-demo"`, and `8` on `"storage-demo"`)[cite: 7, 8, 10, 16].
* Triggered `2` `"high-cpu"` alerts on `"vm-demo"` (`86` and `94` exceeding threshold `85`)[cite: 9].
* Audited `24` chronological events (`monitor logs --limit 25`) spanning `2026-11-23` to `2026-11-25`[cite: 10, 11, 12, 13, 14, 15, 16].

---

## Reproducibility Commands

```bash
cd ~/Desktop/CCSE102_C1126CCSE17867_Lab/lab/lab

# Blob upload, integrity check, and listing
python3 azlocal.py blob upload sticdfalab operations-file --file samples/operations_data.txt
python3 azlocal.py blob verify sticdfalab operations-file
python3 azlocal.py blob list sticdfalab

# Backup creation, VM stop/restore, and listing
python3 azlocal.py backup create known-good
python3 azlocal.py vm stop vm-demo
python3 azlocal.py vm list
python3 azlocal.py backup restore known-good --confirm
python3 azlocal.py vm list

# CPU monitoring rule, sample ingestion, alerts, and audit log review
python3 azlocal.py monitor rule high-cpu --threshold 85
python3 azlocal.py monitor sample
python3 azlocal.py monitor alerts
python3 azlocal.py monitor logs --limit 25

# Evidence report generation and SHA-256 verification
mkdir -p evidence
python3 azlocal.py report --output evidence/cloud_operations_report.json
sha256sum evidence/cloud_operations_report.json
```[cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21, 22]

```
## Evidence & Verification

* **Report Path:** `evidence/cloud_operations_report.json`
* **SHA-256 Digest:** `bebf05ba0fd4b06616111602f2ef18f7240b0ac340bdefd63babd374beff9267`

## Academic Integrity Statement

All simulation runs, security checks, monitoring alerts, and evidence hashes in this repository were executed and documented independently as an offline `CCSE-102` lab exercise without fabricating live cloud telemetry.
