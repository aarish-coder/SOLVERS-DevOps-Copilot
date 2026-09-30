from pathlib import Path
import json


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "services"


def get_service_status(incident_id: str) -> dict:
    """
    Retrieve the current service health information.
    """

    file_path = DATA_DIR / f"{incident_id}.json"

    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (json.JSONDecodeError, OSError):
        return {}