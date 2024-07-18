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

def sum_inf_nd_sup(infnd: np.ndarray, supnd: np.ndarray, patient: str=None) -> np.ndarray:
    """
    Adds up both labels, from inf and sup mouth.
    """
    
    overlap = check_overlap(infnd, supnd)

    if overlap:
        raise Exception(f"""Found overlap in patient {patient if patient else 'UNKNOWN'}, 
                        value of inf: {overlap[0]}, value of sup: {overlap[1]}""")
    
    new_lab_summed = np.zeros_like(infnd)
    new_lab_summed = infnd + supnd

    return new_lab_summed
    
    
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

def process_subject(inf_seg: np.ndarray, sup_seg: np.ndarray,
                    inf_json: Dict[str, int], sup_json: Dict[str, int],
                    skip: Iterable[int]):

    if (inf_seg is not None) and (sup_seg is not None):
        mapped_inf = change_label(seg=inf_seg, mapping=inf_json, skip=skip)
        mapped_sup = change_label(seg=sup_seg, mapping=sup_json, skip=skip)
        summed = sum_inf_nd_sup(mapped_inf, mapped_sup)
        return summed
    elif inf_seg is not None:
        mapped_inf = change_label(seg=inf_seg, mapping=inf_json, skip=skip)
        return mapped_inf
    elif sup_seg is not None:
        mapped_sup = change_label(seg=sup_seg, mapping=sup_json, skip=skip)
        return mapped_sup
    else:
        raise RuntimeError('eh?')


def main():
    args = parse_args()

    niftis = args.niftis
    jsons = args.jsons
    assert len(niftis) == len(jsons), 'Different number of niftis and jsons. Please revise your arguments'
    
    inf_nifti = [i for i in niftis if os.path.basename(i) == 'inf.nii.gz']
    sup_nifti = [i for i in niftis if os.path.basename(i) == 'sup.nii.gz']
    inf_json = [i for i in jsons if os.path.basename(i) == 'inf.json']
    sup_json = [i for i in jsons if os.path.basename(i) == 'sup.json']

    if len(niftis) != 2:
        # check 
        assert not (len(inf_nifti) and len(sup_json)) and not (len(sup_nifti) and len(inf_json)), f'You probably gave a wrong combination of nifti/json ' \
            f'files. Got: \n\t{inf_nifti = }, \n\t{sup_nifti = }, \n\t{inf_json = }, \n\t{sup_json = }' \
            f'\nYou should either give a inf.nii.gz/inf.json pair, or a sup.nii.gz/sup.json pair. Don\'t mix them up!'
        
    # we parse args
    myargs = {}
    try:
        inf_seg, affine = load_nifti(inf_nifti[0], affine=True)
        myargs['inf_seg'] = inf_seg
        inf_json, patient = parse_json_mappings(inf_json[0], True)
        myargs['inf_json'] = inf_json
        out_path = os.path.dirname(inf_nifti[0])
    except IndexError:
        myargs['inf_seg'] = None
        myargs['inf_json'] = None
    try:
        sup_seg, affine = load_nifti(sup_nifti[0], affine=True)
        myargs['sup_seg'] = sup_seg
        sup_json, patient = parse_json_mappings(sup_json[0], True)
        myargs['sup_json'] = sup_json
        out_path = os.path.dirname(sup_nifti[0]) 
    except IndexError:
        myargs['sup_seg'] = None
        myargs['sup_json'] = None

    myargs['skip'] = args.skip

    mapped = process_subject(**myargs)
    
    save_nifti(
        array=mapped, 
        affine=affine,
        out_path=os.path.join(out_path, f'{patient}.nii.gz'),
        dtype=np.uint8
    ) 


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-niftis', required=True, nargs='+', type=str,
                        help='Nifti files to be mapped.')
    parser.add_argument('-jsons', required=True, nargs='+', type=str,
                        help='Json files to do the mapping. Nº niftis and nº jsons HAS to be the same')
    parser.add_argument('-skip', required=False, default=None, nargs='+', type=int,
                        help='add after this argument the integers to skip. E.g.: 1 2 3 4')
    args, unrecognized_args = parser.parse_known_args()
    
    return args
    
if __name__ == "__main__":
    main()