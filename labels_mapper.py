import os
from typing import Iterable, Dict, Union, Tuple, Set
import numpy as np
from utils import *

def change_label(seg: np.ndarray, 
                 mapping: Dict[str, int], 
                 skip: Iterable[int] = None) -> np.ndarray:
    """
    Gets a 3d array with label values. Changes them according to mapping.
    ---
    param: 
        skip: Iterable with ints corresponding to classes that will be removed from seg
    """

    out = np.zeros_like(seg)
    for k, v in mapping.items():
        out[seg==int(k)] = int(v)
    
    if skip is not None:
        skip = list(set(skip))
        out[np.isin(out, skip)] = 0

    return out

def check_overlap(infnd: np.ndarray, supnd: np.ndarray) -> Union[None, np.ndarray]:
    """Bins two labels and checks if there is any overlap"""
    binned_inf = np.zeros_like(infnd)
    binned_inf[infnd!=0] = 1
    binned_sup = np.zeros_like(supnd)
    binned_sup[supnd!=0] = 1

    sum = binned_inf + binned_sup

    overlap = np.any(sum>1)

    if overlap:
        where = np.where(sum > 1)
        return infnd[where], supnd[where]

    return 

def sum_inf_nd_sup(infnd: np.ndarray, supnd: np.ndarray, patient:str) -> np.ndarray:
    """
    Adds up both labels, from inf and sup mouth.
    """
    
    overlap = check_overlap(infnd, supnd)

    if overlap:
        raise Exception(f"""Found overlap in patient {patient}, 
                        value of inf: {overlap[0]}, value of sup: {overlap[1]}""")
    
    new_lab_summed = np.zeros_like(infnd)
    new_lab_summed = infnd + supnd

    return new_lab_summed

def process_two_mouths_sep(case_path: str, patient: str, dtype, skip: Set[int] = None,
                           rater: str = None, return_rater: bool = False,) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    This won't be necessary in the future. We'll be dealing with full mouths.
    """
    if rater is None:
        raters_av = os.listdir(os.path.join(case_path, 'labels'))
        rater = decide_rater(raters_av)

    label_path = os.path.join(case_path, 'labels',rater)

    twomouths = subfiles(folder=label_path, join=True, suffix=('inf.nii.gz', 'sup.nii.gz'))

    # which mouths are there in the folder?
    doinf = False; dosup = False; doboth = False
    if len(twomouths) == 2: doboth = True
    elif os.path.join(label_path, 'inf.nii.gz') in twomouths: doinf = True
    elif os.path.join(label_path, 'sup.nii.gz') in twomouths: dosup = True
    else: raise RuntimeError(f'No mask found in case {case_path}')

    if doboth:
        classesinf = parse_json_mappings(file=os.path.join(case_path, 'labels', rater, 'json_mappings', 'inf.json'))
        classessup = parse_json_mappings(file=os.path.join(case_path, 'labels', rater, 'json_mappings', 'sup.json'))
        # assert patientfromjsoninf == patient == patientfromjsoninf, f"Patients dont match." \
        #     f"Got {patientfromjsoninf}, {patient}, {patientfromjsonsup}"

        inf_mask = os.path.join(case_path, 'labels', rater, 'inf.nii.gz')
        sup_mask = os.path.join(case_path, 'labels', rater, 'sup.nii.gz')

        infnd, infaffine = load_nifti(inf_mask, True)
        supnd, supaffine = load_nifti(sup_mask, True)
        assert np.allclose(supaffine, infaffine, atol=1e-5), \
            f'Affines for sup and inf mouths don\'t match in case {case_path}. {print(supaffine, infaffine)}'
        
        newlabinf = change_label(infnd, classesinf, skip)
        newlabsup = change_label(supnd, classessup, skip)
        summed = sum_inf_nd_sup(newlabinf, newlabsup, patient=patient)
        if return_rater:
            return summed.astype(dtype), infaffine, rater
        return summed.astype(dtype), infaffine

    elif doinf: 
        classesinf = parse_json_mappings(file=os.path.join(case_path, 'labels', rater, 'json_mappings', 'inf.json'))
        inf_mask = os.path.join(case_path, 'labels', rater, 'inf.nii.gz')
        
        infnd, affine = load_nifti(inf_mask, True)
        newlabinf = change_label(infnd, classesinf, skip)
        if return_rater:
            return newlabinf.astype(dtype), affine, rater
        return newlabinf.astype(dtype), affine

    elif dosup: 
        classessup = parse_json_mappings(file=os.path.join(case_path, 'labels', rater, 'json_mappings', 'sup.json'))
        sup_mask = os.path.join(case_path, 'labels', rater, 'sup.nii.gz')
        supnd, affine = load_nifti(sup_mask, affine=True)
        newlabsup = change_label(supnd, classessup, skip)
        if return_rater:
            return newlabsup.astype(dtype), affine, rater
        return newlabsup.astype(dtype), affine

    else:
        raise Exception(f"WTF! Case: {case_path}")
    
def mapteeth_to_n(oldteethnd: np.ndarray, 
                  to_change: Set[int], 
                  n: Union[int, Set[int]], 
                  copy: bool=True) -> np.ndarray:
    """
    Converts label values that are in a set of values (in my case the set represents teeth) 
    to a new id (label value).

    Parameters
    ------------
    oldteethnd: np.ndarray
        Input array that we have to change its values
    to_change: set
        set containing the values that will be mapped to n
    n: int

    Returns
    ------------
    New array with mapping done (np.ndarray)
    """

    # I hate myself
    if isinstance(n, set):
        assert len(n) == 1, f"WTF?? {n = }"
        n = list(n)[0]
        
    # we copy the array not to fuck up the original one
    mapped_nd = oldteethnd.copy() if copy else oldteethnd    
    mapped_nd[np.isin(oldteethnd, list(to_change))] = n
    
    return mapped_nd