# P110 Energy Logger

Logs energy data from TP-Link Tapo P110 smart plugs to a local JSON file. No cloud, no dashboard.

## Install & Run

```bash
pip install git+https://github.com/ZeliardM/python-kasa.git@feature/tpap pyyaml
```

**Linux/macOS:**
```bash
export TAPO_EMAIL=you@email.com TAPO_PASSWORD=yourpass
python main.py --config tapo.yaml --out energy.json --interval 60
```

**Windows (PowerShell):**
```powershell
$env:TAPO_EMAIL="you@email.com"
$env:TAPO_PASSWORD="yourpass"
python main.py --config tapo.yaml --out energy.json --interval 60
```
