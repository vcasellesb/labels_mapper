import os
import re

# we allow three situations:
# * {subject_path} is given
# * {subject_path}/labels is given
# * {subject_path}/labels/RX is given
# We assume the latter, and if wrong work our way backwards

COMMON_REGEX = r'(?P<loc>inf|sup)'
NIFTI_REGEX = COMMON_REGEX + r'.*\.nii(?:.gz)?'
JSON_REGEX = COMMON_REGEX + r'.*\.json'
_REGEX = r'(?P<loc>inf|sup).*\.(?P<file>nii|json)'
_REGEX_STRICT = r'(?P<loc>inf|sup)\.(?P<file>nii|json)'

def get_regex(nifti: bool, strict: bool) -> re.Pattern:
    regex_string = COMMON_REGEX
    if strict:
        regex_string += r'\.'
    else:
        regex_string += r'.*\.'
    if nifti:
        regex_string += r'nii(?:.gz)?'
    else:
        regex_string += r'json'
    return re.compile(regex_string)

def _filter_iterable_with_regex(iterable, regex: re.Pattern):
    return filter(None, map(lambda x: regex.search(x), iterable))

def list_and_join(folder: str):
    return list(map(lambda x: os.path.join(folder, x), os.listdir(folder)))

def list_join_and_filter(folder: str, regex: re.Pattern | str = None) -> list[re.Match]:
    if isinstance(regex, str):
        regex = re.compile(regex)
    f = lambda x: x
    if regex is not None:
        f = lambda x: regex.search(x)
    return list(
        filter(
            None,
            map(
                f,
                map(lambda x: os.path.join(folder, x), os.listdir(folder))
            )
        )
    )

def _get_niftis(folder, strict: bool = False):
    return list_join_and_filter(folder, get_regex(True, strict))

def get_jsons(folder, strict: bool = False):
    return list_join_and_filter(folder, get_regex(False, strict))

def get_json_mappings(folder):

    to_try = (
        lambda: get_jsons(folder, True), 
        lambda: get_jsons(folder, False)
    )
    if os.path.isdir(os.path.join(folder, 'json_mappings')):
        to_try = (
            lambda: get_jsons(os.path.join(folder, 'json_mappings'), True),
            lambda: get_jsons(os.path.join(folder, 'json_mappings'), False)
        ) + to_try

    i = 0
    jsons = []
    while not len(jsons):
        if i >= len(to_try):
            raise FileNotFoundError(folder)
        jsons = to_try[i]()
        i += 1
    return jsons

def get_niftis(folder, n):
    niftis = _get_niftis(folder, False)
    if len(niftis) != n:
        niftis = _get_niftis(folder, True)
    return niftis

def sort_args(list_of_matches1: list[re.Match], list_of_matches2: list[re.Match]) -> list[tuple[str, str]]:
    assert len(list_of_matches1) == len(list_of_matches2)
    output = []
    for i in range(len(list_of_matches1)):
        this_group = list_of_matches1[i].group('loc')
        output.append(
            (list_of_matches1[i].string, 
             next(i.string for i in list_of_matches2 if i.group('loc') == this_group))
        )
    return output


def get_args_from_folder(folder) -> list[tuple[str, str]]:
    jsons = get_json_mappings(folder)
    n = len(jsons)
    niftis = get_niftis(folder, n)
    return sort_args(niftis, jsons)


def list_and_maybe_extend_with_json_mappings(folder: str):
    listed_folder = list_and_join(folder)
    _dirs = [i for i in listed_folder if os.path.isdir(i)]
    if len(_dirs):
        assert len(_dirs) == 1
        listed_folder.extend(list_and_join(_dirs[0]))
    return listed_folder

def _get_args_dict_from_folder(folder: str, regex: re.Pattern) -> list[tuple[str, str]]:
    files = list_and_maybe_extend_with_json_mappings(folder)
    files = list(_filter_iterable_with_regex(files, regex))
    results = []
    for i in range(len(files) - 1):
        for j in range(i+1, len(files)):
            if files[i].group('loc') == files[j].group('loc'):
                results.append((files[i].string, files[j].string))
                if files[j].group('file') != 'json':
                    results[-1] = results[-1][::-1]
                break
    return results

def get_args_dict_from_folder(folder: str) -> list[tuple[str, str]]:
    reg = re.compile(_REGEX_STRICT)
    files = _get_args_dict_from_folder(folder, reg)
    if len(files) == 0:
        reg = re.compile(_REGEX)
        files = _get_args_dict_from_folder(folder, reg)
    return files

_RATERS_ORDER = ('R6', 'R3', 'R2', 'R4', 'R1')
def get_rater_folder(folder: str):
    for rater in _RATERS_ORDER:
        this_folder = os.path.join(folder, rater)
        if os.path.exists(this_folder):
            return this_folder
    raise FileNotFoundError(folder)

def get_args(folder: str):
    """Assume we are at folder/labels/RX, go backward"""
    to_try = (
        lambda: get_args_from_folder(folder),
        lambda: get_args_from_folder(get_rater_folder(folder)),
        lambda: get_args_from_folder(get_rater_folder(os.path.join(folder, 'labels')))
    )
    to_try = iter(to_try)
    exceptions = []
    while True:
        try:
            this_try = next(to_try)()
        except (FileNotFoundError, AssertionError) as e:
            exceptions.append(e)
            continue
        except StopIteration as e:
            msg = (
                'No valid inputs found! Tried the following folders:\n' +
                ('%s\n' * len(exceptions)) % tuple(str(x) for x in exceptions)
            )
            raise FileNotFoundError(msg) from e
        return this_try


if __name__ == "__main__":
    import sys
    try1 = get_args('test-data/#14/labels/R1')
    try2 = get_args('test-data/#14/labels')
    try3 = get_args('test-data/#14')

    assert all(i == j == z for i, j, z in zip(try1, try2, try3))