def summaryEntity(item) -> dict:
    return{
        "id":str(item["_id"]),
        "id_of_video":item["id_of_video"],
        "summary":item["summary"],
        "AI_used":item["AI_used"]
    }

def summariesEntity(entity) -> list:
    return[summaryEntity(item) for item in entity]