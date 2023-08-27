page_to_keyword_map = {}


def get_keyword_to_page_map():
    result = {}
    for k, vals in page_to_keyword_map.items():
        for v in vals:
            result[v] = k
    return result
