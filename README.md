# P110 Energy Logger

Logs energy data from TP-Link Tapo P110 smart plugs to a local JSON file. No cloud, no dashboard, no dependencies beyond python-kasa and pyyaml.

## Install & Run

```bash
pip install git+https://github.com/ZeliardM/python-kasa.git@feature/tpap pyyaml
export TAPO_EMAIL=you@email.com TAPO_PASSWORD=yourpass
python main.py --config tapo.yaml --out energy.json --interval 60
```
