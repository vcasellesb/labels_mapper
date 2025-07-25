import json, os
from typing import Union, Dict, Tuple, Iterable, List
import numpy as np
import nibabel as nib


def load_nifti(path: str) -> Tuple[np.ndarray, ...]:
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

def parse_json_mappings(file: str, return_patient: bool = False) -> \
    Union[Dict[str, int], Tuple[Dict[str, int], str]]:
    """
    Gets a json file path and returns the dictionary with labels
    This dictionary has the array values as keys and the actual teeth label as values.
    """
    
    dict_raw = load_json(file)
    labels: dict = dict_raw["labels_mapping"]
    if not return_patient:
        return labels
    
    ## I'm dumb
    try:
        patient: str = dict_raw['patient_name']
    except KeyError:
        patient: str = dict_raw['patient']
    return labels, patient

def load_json(file: str):
    with open(file, 'r') as f:
        a = json.load(f)
    return a

def determine_maxval(*dicts_with_labels: Dict[str, int] | None) -> int | None:
    maxval = None
    for d in dicts_with_labels:
        if d is not None:
            maxval = max(d.values())
    
    return maxval

def subfiles(folder: str, join: bool = True,
             prefix: str = None, suffix: str = None,
             sort: bool = True, exclude: Union[str, Iterable] = None) -> List[str]:
    
    if join:
        l = os.path.join
    else:
        l = lambda x, y: y
    
    if exclude:
        # since os.listdir only returns basename, in order to be able to compare
        # strings consistently we have to convert all exclude args to basename
        if isinstance(exclude, str):
            exclude = [os.path.basename(exclude)]
        elif isinstance(exclude, Iterable):
            exclude = [os.path.basename(e) for e in exclude]
        else:
            raise TypeError(f'Invalid exlude type. Got {type(exclude)}, expected either str or Iterable')

    res = [l(folder, i) for i in os.listdir(folder) if os.path.isfile(os.path.join(folder, i))
           and (prefix is None or i.startswith(prefix))
           and (suffix is None or i.endswith(suffix))
           and (exclude is None or not any([ex in i for ex in exclude]))]
    if sort:
        res.sort()
    return res

if __name__ == "__main__":

    maxval = determine_maxval({'1': 24, '2': 38, "4": 1})
    assert maxval == 38

    maxval = determine_maxval({'1': 24, '2': 38, "4": 1}, {'5': 84, '3': 2})
    assert maxval == 84