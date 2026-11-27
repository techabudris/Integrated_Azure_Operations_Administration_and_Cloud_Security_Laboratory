# Lab 02 - Compute, network rules and a real Linux service

```bash
python3 azlocal.py vm create vm-demo --group rg-icdfa-lab --size B1s
python3 azlocal.py vm start vm-demo
python3 azlocal.py vm list
python3 azlocal.py nsg create nsg-demo --group rg-icdfa-lab
python3 azlocal.py nsg rule nsg-demo --source 192.168.56.0/24 --port 22 --decision allow --priority 100
python3 azlocal.py nsg test nsg-demo --source 192.168.56.20 --port 22
python3 azlocal.py nsg test nsg-demo --source 203.0.113.20 --port 22
python3 azlocal.py nsg rule nsg-demo --source 0.0.0.0/0 --port 22 --decision allow --priority 200
python3 azlocal.py policy
python3 azlocal.py nsg remove nsg-demo --priority 200
python3 azlocal.py policy
```

The VM commands change simulated inventory only. To administer a **real Linux process**, run in a second terminal:

```bash
python3 scripts/health_service.py --port 8088
```

In a new terminal:

```bash
curl http://127.0.0.1:8088/health
ss -ltn | grep 8088
```

Optional two-machine mode: run service on a dedicated Ubuntu Server VM and forward it privately:

```bash
ssh -L 8088:127.0.0.1:8088 <user>@<private-server-ip>
curl http://127.0.0.1:8088/health
```

Tasks: compare allowed/denied NSG decisions, identify risky wildcard SSH rule, remove the rule, show real localhost service works. Avoid production network changes.

Evidence: VM record, NSG evaluation results, policy before/after, service curl result, terminal `ss` output.
