from sqlalchemy import inspect


def to_dict(obj):
    if obj is None:
        return None
    d = {}
    for col in inspect(obj.__class__).columns:
        val = getattr(obj, col.name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        d[col.name] = val
    return d


def to_list(objs):
    return [to_dict(o) for o in objs]
