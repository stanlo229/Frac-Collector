import yaml
import os

DEFAULT_WASTE_YAML_PATH = os.path.join(os.path.dirname(__file__), "vial_status.yaml")


class WasteVialTracker:
    """Track waste vials with 3.5 mL capacity per vial.
    
    Tracks which waste vial is currently active and how much liquid has been
    dispensed into it. When a vial reaches 3.5 mL, automatically switches to
    the next vial.
    
    Stores state in the "waste_vials" section of vial_status.yaml for consistency.
    """

    def __init__(self, yaml_path: str = DEFAULT_WASTE_YAML_PATH, num_waste_vials: int = 3, capacity_ml: float = 3.5):
        self.yaml_path = yaml_path
        self.num_waste_vials = num_waste_vials
        self.capacity_ml = capacity_ml
        self.current_vial_index = 0
        self.current_volume_ml = 0.0
        self.vials = []

        if os.path.exists(yaml_path):
            self._load()
        else:
            self._initialize()
            self._save()
            print(f"Waste vial tracker initialized: {self.yaml_path}")

    # ---- Internal ----

    def _initialize(self):
        """Initialize state: all vials empty, start at vial 0."""
        self.vials = [
            {"index": i, "volume_ml": 0.0, "full": False}
            for i in range(self.num_waste_vials)
        ]
        self.current_vial_index = 0

    def _load(self):
        """Load state from YAML waste_vials section and read global capacity_ml."""
        with open(self.yaml_path, "r") as f:
            full_data = yaml.safe_load(f) or {}
        
        # Load global capacity_ml if available
        capacity_config = full_data.get("capacity_ml", {})
        global_capacity = capacity_config.get("waste_vials", 3.5)
        self.capacity_ml = global_capacity
        
        waste_data = full_data.get("waste_vials", {})
        self.vials = waste_data.get("vials", [])
        self.current_vial_index = waste_data.get("current_vial_index", 0)
        
        # Ensure correct number of vials
        while len(self.vials) < self.num_waste_vials:
            i = len(self.vials)
            self.vials.append({"index": i, "volume_ml": 0.0, "full": False})
        
        self.vials = self.vials[:self.num_waste_vials]

        # Bound current index
        if self.current_vial_index >= self.num_waste_vials:
            self.current_vial_index = self.num_waste_vials - 1

        # Recalculate current volume from current vial
        if self.vials:
            self.current_volume_ml = self.vials[self.current_vial_index].get("volume_ml", 0.0)

    def _save(self):
        """Persist state to YAML waste_vials section, preserving global capacity_ml."""
        # Load full file to preserve all sections
        if os.path.exists(self.yaml_path):
            with open(self.yaml_path, "r") as f:
                full_data = yaml.safe_load(f) or {}
        else:
            full_data = {}
        
        # Ensure global capacity_ml config exists and is updated
        if "capacity_ml" not in full_data:
            full_data["capacity_ml"] = {}
        if "sample_vials" not in full_data["capacity_ml"]:
            full_data["capacity_ml"]["sample_vials"] = 1.2  # default
        full_data["capacity_ml"]["waste_vials"] = self.capacity_ml
        
        # Update waste_vials section (capacity_ml is now in global config)
        full_data["waste_vials"] = {
            "current_vial_index": self.current_vial_index,
            "vials": self.vials,
        }
        
        # Write back
        with open(self.yaml_path, "w") as f:
            yaml.dump(full_data, f, default_flow_style=False, allow_unicode=True)

    # ---- Public API ----

    def add_volume(self, volume_ml: float) -> bool:
        """Record waste liquid added.
        
        Returns:
            True if vial is still available for more liquid
            False if this addition would exceed capacity (warning issued but volume recorded)
        """
        if self.current_vial_index >= self.num_waste_vials:
            print(f"WARNING: All {self.num_waste_vials} waste vials are full!")
            return False

        self.current_volume_ml += volume_ml
        self.vials[self.current_vial_index]["volume_ml"] = round(self.current_volume_ml, 4)

        if self.current_volume_ml >= self.capacity_ml:
            self.vials[self.current_vial_index]["full"] = True
            print(
                f"Waste vial {self.current_vial_index} is full "
                f"({self.current_volume_ml:.2f} mL >= {self.capacity_ml:.2f} mL capacity)."
            )
            self._advance_to_next_vial()
            return self.current_vial_index < self.num_waste_vials

        self._save()
        return True

    def _advance_to_next_vial(self):
        """Move to the next available waste vial."""
        self.current_vial_index += 1
        if self.current_vial_index < self.num_waste_vials:
            self.current_volume_ml = self.vials[self.current_vial_index].get("volume_ml", 0.0)
            print(f"Advanced to waste vial {self.current_vial_index}.")
        else:
            print(f"No more waste vials available (used all {self.num_waste_vials}).")
        self._save()

    def get_current_vial(self) -> int:
        """Return the current active waste vial index (0-based)."""
        return self.current_vial_index

    def get_current_volume(self) -> float:
        """Return the current volume in the active waste vial."""
        return self.current_volume_ml

    def get_remaining_capacity_ml(self) -> float:
        """Return remaining capacity in current waste vial."""
        if self.current_vial_index >= self.num_waste_vials:
            return 0.0
        return max(0.0, self.capacity_ml - self.current_volume_ml)

    def get_total_waste_capacity_ml(self) -> float:
        """Return total remaining capacity across all waste vials."""
        total = 0.0
        for i in range(self.current_vial_index, self.num_waste_vials):
            if i == self.current_vial_index:
                total += self.get_remaining_capacity_ml()
            else:
                total += self.capacity_ml
        return total

    def is_full(self) -> bool:
        """Return True if all waste vials are full."""
        return self.current_vial_index >= self.num_waste_vials

    def summary(self) -> dict:
        """Return a dict with tracking info."""
        return {
            "current_vial": self.current_vial_index,
            "current_volume_ml": round(self.current_volume_ml, 4),
            "remaining_capacity_ml": round(self.get_remaining_capacity_ml(), 4),
            "total_remaining_capacity_ml": round(self.get_total_waste_capacity_ml(), 4),
            "all_full": self.is_full(),
            "vials": [dict(v) for v in self.vials],
        }

    def reset(self):
        """Clear all waste vial tracking."""
        self._initialize()
        self._save()
        print(f"Waste vial tracker reset: {self.num_waste_vials} vials cleared.")
