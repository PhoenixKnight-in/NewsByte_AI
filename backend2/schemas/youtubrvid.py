def vidEntity(item) -> dict:
    return{
        "id":str(item["_id"]),
        "title":item["title"],
        "desc":item["desc"],
        "link":item["link"],
        "thumbnail":item["thumbnail"],
        "duration":item["duration"],
        "upload_date":item["upload_date"],
        "transcript":item["transcript"],
    }

def vidsEntity(entity) -> list:
    return[vidEntity(item) for item in entity]