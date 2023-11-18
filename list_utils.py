def str_to_list(data: str) -> list[tuple[str, str, str, float]]:
    data = data.strip()
    if not (data.startswith("[") and data.endswith("]")):
        raise ValueError(f"Cannot decode {data}")
    
    if data == "[]":
        return []

    res = []
    data = data.strip("[").strip("]")
    for tpl in data.split("("):
        if not tpl:
            continue

        uid, msg, user, time = tpl.strip("), ").replace("'", "").split(", ")
        time = float(time)
        res.append((uid, msg, user, time))
    
    return res

def unify_lists(list1: list[tuple[str, str, str, float]], list2: list[tuple[str, str, str, float]]) -> list[tuple[str, str, str, float]]:
    uids = [item[0] for item in list1]

    for line in list2:
        # the element already exists
        if line in list1:
            continue

        # the element is new
        if line[0] not in uids:
            list1.append(line)
            uids = [item[0] for item in list1]
            continue

        # the element has changed
        if line[0] in uids:
            curr_line = list1[uids.index(line[0])]

            # the current element is newer
            if curr_line[3] > line[3]:
                continue

            # the new element is newer
            list1[uids.index(line[0])] = line
            uids = [item[0] for item in list1]

    return list1
