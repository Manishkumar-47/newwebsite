import json
import re
from typing import Any


def load_json_from_model(content: str) -> Any:
    """Parse JSON from a model response, accepting plain JSON or fenced JSON."""
    stripped = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    array_start = stripped.find("[")
    array_end = stripped.rfind("]")
    if array_start != -1 and array_end != -1 and array_end > array_start:
        return json.loads(stripped[array_start : array_end + 1])

    object_start = stripped.find("{")
    object_end = stripped.rfind("}")
    if object_start != -1 and object_end != -1 and object_end > object_start:
        return json.loads(stripped[object_start : object_end + 1])

    raise ValueError("No valid JSON object or array found in model response.")

