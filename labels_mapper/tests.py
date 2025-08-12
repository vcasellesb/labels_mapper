import os
from .folder_stuff import list_join_and_filter, _REGEX_STRICT, get_args
from .utils import sanity_check_json

TEST_DATA = 'test-data'
def naive_joiner(folder):
    return [os.path.join(folder, x) for x in os.listdir(folder) if x.endswith(('.json', '.nii', '.nii.gz'))]
def test_join_and_filter():
    folder1 = '%s/006_/labels/R6' % TEST_DATA
    got = list_join_and_filter(folder1, _REGEX_STRICT)
    assert set(got) == set(naive_joiner(folder1)), '%s\n%s' % (got, naive_joiner(folder1))

    folder2 = '%/036_/labels/R3' % TEST_DATA
    got = list_join_and_filter(folder2, _REGEX_STRICT)
    assert set(got) == set(naive_joiner(folder2))

def test_get_args():
    folder1 = '%s/006_/labels/R6' % TEST_DATA
    folder2 = '%s/006_/labels' % TEST_DATA
    folder3 = '%s/006_' % TEST_DATA
    try1 = get_args(folder1)
    try2 = get_args(folder2)
    try3 = get_args(folder3)
    assert all(i == j == z for i, j, z in zip(try1, try2, try3))

    folder1 = '%s/036_/labels/R3' % TEST_DATA
    folder2 = '%s/036_/labels' % TEST_DATA
    folder3 = '%s/036_' % TEST_DATA
    try1 = get_args(folder1)
    try2 = get_args(folder2)
    try3 = get_args(folder3)
    assert all(i == j == z for i, j, z in zip(try1, try2, try3))

def test_sanity_checks():
    sanity_check_json({'1': 40, '10': 42, '10': 30, '3': 40})


if __name__ == "__main__":
    # test_join_and_filter()
    test_get_args()
    test_sanity_checks()