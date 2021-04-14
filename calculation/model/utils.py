def dotted_string_to_list(data):
    return [int(x) for x in data.split('.')]


def list_to_dotted_string(data):
    return '.'.join(data)
