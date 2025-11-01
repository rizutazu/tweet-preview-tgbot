import os

def getToken() -> str:
    raw = os.getenv("TOKEN")
    if not isinstance(raw, str):
        return ""
    return raw

def getAllowedIds() -> list[int]:
    raw = os.getenv("ALLOWED_IDS")
    if not isinstance(raw, str):
        return []
    else:
        raw = raw.split(",")

    result = []
    
    for id in raw:
        try:
            result.append(int(id.strip()))
        except:
            continue
    
    return list(set(result))