import yaml
from pathlib import Path

YAML_PATH = Path(__file__).parent / "vial_status.yaml"
NUM_VIALS = 48

def _vial_name(i, num_y=8):
    return chr(ord('A') + i // num_y) + str(i % num_y + 1)

# Read existing file so we can preserve capacity_ml and waste vial count
existing = {}
if YAML_PATH.exists():
    with open(YAML_PATH) as f:
        existing = yaml.safe_load(f) or {}

capacity_ml = existing.get("capacity_ml", {"sample_vials": 1.2, "waste_vials": 3.5})

num_waste_vials = len((existing.get("waste_vials") or {}).get("vials", [{"index": 0}, {"index": 1}]))

data = {
    "capacity_ml": capacity_ml,
    "sample_vials": [
        {"index": i, "vial_name": _vial_name(i), "label": "", "reaction_name": "", "volume_ml": 0.0}
        for i in range(NUM_VIALS)
    ],
    "waste_vials": {
        "current_vial_index": 0,
        "vials": [
            {"index": i, "full": False, "volume_ml": 0.0}
            for i in range(num_waste_vials)
        ],
    },
}

with open(YAML_PATH, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Reset {NUM_VIALS} sample vials and {num_waste_vials} waste vials in {YAML_PATH}")
