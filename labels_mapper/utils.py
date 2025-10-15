import json, os
from typing import Union, Dict, Tuple
import numpy as np
import nibabel as nib
import warnings


def load_nifti(path: str) -> Tuple[np.ndarray, np.ndarray, nib.Nifti1Header]:
    """
    Helper to easily load nifti files.
    """
    nifti: nib.Nifti1Image = nib.load(path)
    array = np.asanyarray(nifti.dataobj)

    return array, nifti.affine, nifti.header


def save_nifti(array: np.ndarray,
               affine: np.ndarray,
               out_path: str,
               header = None,
               overwrite: bool = False,
               dtype = None):
    if os.path.exists(out_path) and not overwrite:
        raise FileExistsError(f'File {out_path} exists and overwrite is set to False')
    outnii = nib.Nifti1Image(array, affine, header)
    if dtype is not None:
        outnii.set_data_dtype(dtype)
    nib.save(outnii, out_path)


def parse_json_mappings(file: str) -> Tuple[Dict[int, int], Union[str, None]]:
    """
    Gets a json file path and returns the dictionary with labels
    This dictionary has the array values as keys and the actual teeth label as values.
    """

    dict_raw = load_json(file)
    if 'labels_mapping' not in dict_raw:
        raise KeyError('labels_mapping missing in file %s' % file)
    labels: dict = {int(k): int(v) for k, v in dict_raw['labels_mapping'].items()}
    return labels, dict_raw.get('patient_name') or dict_raw.get('patient')

def load_json(file: str):
    with open(file, 'r') as f:
        a = json.load(f)
    return a

def determine_maxval(*dicts_with_labels: Dict[str, int] | None) -> int | None:
    vals = []
    for d in dicts_with_labels:
        vals.extend([] if d is None else d.values())
    return max(vals, default=None)

def determine_maxval2(*dicts_with_labels: Dict[str, int] | None) -> int | None:
    maxval = None
    for d in dicts_with_labels:
        if d is None:
            continue
        tmp = max(d.values())
        if maxval is None or tmp > maxval:
            maxval = tmp

    return maxval

_ACCEPTED_VALUES = {1, 2, 3} | set(range(11, 49))

def sanity_check_json(json_mapping: dict[str, int]) -> None:
    """ 
    Checks:
    * values follow ISO 3950
    * unique dict values
    """
    vals = json_mapping.values()
    if any(v not in _ACCEPTED_VALUES for v in vals):
        msg = (
            'Unexpected value in the provided json:\n' +
            [v for v in vals if v not in _ACCEPTED_VALUES].__str__()
        )
        raise ValueError(msg)

    if len(set(vals)) != len(vals):
        msg = (
            'Found non-unique values in the provided json! It\'s up to you if this is a problem. The values are:\n'
        )
        repeated_vals = set(i for i in vals if sum(j == i for j in vals) > 1)
        warnings.warn(msg + list(repeated_vals).__str__())

    keys = json_mapping.keys()
    if len(set(keys)) != len(keys):
        msg = (
            'Found non-unique keys in the provided json! It\'s up to you if this is a problem. The keys are:\n'
        )
        repeated_keys = set(i for i in keys if sum(j == i for j in keys) > 1)
        warnings.warn(msg + list(repeated_keys).__str__())


if __name__ == "__main__":

    maxval = determine_maxval({'1': 24, '2': 38, "4": 1})
    assert maxval == 38, maxval

    dicts = ({'1': 24, '2': 38, "4": 1}, {'5': 84, '3': 2}, {"1": 2, "3": 4})
    maxval = determine_maxval(*dicts)
    assert maxval == 84

    maxval = determine_maxval2({'1': 24, '2': 38, "4": 1})
    assert maxval == 38, maxval

    dicts = ({'1': 24, '2': 38, "4": 1}, {'5': 84, '3': 2}, {"1": 2, "3": 4})
    maxval = determine_maxval2(*dicts)
    assert maxval == 84