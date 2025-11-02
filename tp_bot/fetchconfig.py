import os

def getToken() -> str:
    raw = os.getenv("TOKEN", "")
    return raw

def getAllowedIds() -> list[int]:
    raw = os.getenv("ALLOWED_IDS")
    if raw == None:
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