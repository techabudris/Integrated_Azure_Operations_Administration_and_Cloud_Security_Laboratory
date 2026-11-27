# ICDFA CCSE-102 - Azure Operations & Administration
## Linux-only practical laboratory (OFFLINE SIMULATION)

Read `Student_Training_Manual.pdf` before starting.

This package does not use Microsoft Azure, Azure CLI, Azure credits, an Azure tenant or Microsoft's hosted labs. It provides a locally controlled teaching simulator that reproduces selected administration concepts, not actual Azure resources.

## Start on Ubuntu, Debian, Fedora or another Linux distribution

1. Open Terminal in the extracted `lab` directory.
2. Verify Python: `python3 --version` (3.10+).
3. Initialise: `python3 azlocal.py init`.
4. Examine commands: `python3 azlocal.py --help`.
5. Follow the four lab guides in `guides/`.
6. Create evidence under a new `evidence/` folder, and keep your own screenshots and written findings.
7. Complete the `templates/individual_evidence_log.md` and `templates/risk_register.csv`.
8. Submit your PDF report and GitHub repository containing your own evidence. Never commit secrets or a real cloud tenant configuration.

If you have an additional Ubuntu Server VM, SSH into it from your Linux workstation and run the same CLI there. A single Linux computer is sufficient if the VM option is unavailable.

The `workspace` directory stores local state and is created after `init`. Do not distribute it with your submission if it contains personal information.

## Real Linux service option

Start `python3 scripts/health_service.py --port 8088` in one terminal.
From another terminal run `curl http://127.0.0.1:8088/health`.
The service listens on localhost only. When using an Ubuntu Server VM, forward that port through SSH:
`ssh -L 8088:127.0.0.1:8088 <user>@<private-server-ip>`
Then browse `http://127.0.0.1:8088/health` on the workstation.

Do not expose port 8088 publicly and do not use production systems.
