def lessons_list_key():
    return "lessons:list"


def lesson_detail_key(lesson_id: int):
    return f"lesson:{lesson_id}"


def availability_key(lesson_id: int, date_str: str):
    return f"avail:{lesson_id}:{date_str}"