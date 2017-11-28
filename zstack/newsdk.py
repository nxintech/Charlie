

def find_variables_in_path(path):
    """
    :type path: str
    :return: variables list
    """
    if not isinstance(path, str):
        raise TypeError("path is not str")

    if path == '':
        raise ValueError('empty path')

    if not path.startswith('/'):
        raise ValueError("must startswith '/' in '{}'".format(path))

    subs = path.split('/')

    result = []

    for i, sub in enumerate(subs):  # subs[1:] remove '' before /
        if sub == '' and i != 0 and i != len(subs) - 1:
            raise ValueError("empty char between slash in '{}'".format(path))

        if '{' not in sub and '}' not in sub:
            continue

        left_count, right_count = sub.count('{'), sub.count('}')
        if left_count == 0 and right_count == 0:
            continue

        if left_count != right_count:
            raise ValueError("brace pair not match in '{}'".format(path))

        elif left_count != 1:
            raise ValueError("too many braces in '{}'".format(path))

        variable = sub[sub.find('{') + 1: sub.find('}')]

        if len(variable) == 0:
            raise ValueError("emtpy variable in '{}'".format(path))

        result.append(variable)

    return result


class PathAttribute:
    name = 'liu'
    age = 28

    def replace(self, path):
        replaced_path = path
        return replaced_path
