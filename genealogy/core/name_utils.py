def infer_full_name(name: str, current_last_name: str) -> str:
    """
    If the name is a single word, append the current_last_name.
    Otherwise, return the name as is.
    """
    if not name or not current_last_name:
        return name
    parts = name.split()
    if len(parts) == 1:
        return f"{name} {current_last_name}"
    return name 