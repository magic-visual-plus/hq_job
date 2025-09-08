import json

def to_str(v):
    if isinstance(v, str):
        return v
    elif isinstance(v, int) or isinstance(v, float):
        return str(v)
    elif isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)
    elif isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    else:
        raise ValueError(f"Unsupported type for to_str: {type(v)}")
    pass


def from_str(v, target_type):
    if target_type == str:
        return v
    elif target_type == int:
        return int(v)
    elif target_type == float:
        return float(v)
    elif target_type == list:
        return json.loads(v)
    elif target_type == dict:
        return json.loads(v)
    else:
        raise ValueError(f"Unsupported target_type for from_str: {target_type}")
    pass