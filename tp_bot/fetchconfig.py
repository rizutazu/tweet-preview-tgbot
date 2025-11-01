import os

def getToken() -> str:
    return os.getenv("TOKEN")

def getAllowedIds() -> list[int]:
    raw = os.getenv("ALLOWED_IDS").split(",")
    result = []
    
    for id in raw:
        try:
            result.append(int(id.strip()))
        except:
            continue
    
    return list(set(result))