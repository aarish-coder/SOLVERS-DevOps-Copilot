from pathlib import Path
import json


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "logs"


def get_logs(incident_id: str) -> list[dict]:
    """
    Retrieve logs related to an incident.
    Looks for <incident_id>.json inside data/logs/.
    """

    file_path = DATA_DIR / f"{incident_id}.json"

    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else [data]

    except (json.JSONDecodeError, OSError):
        return []