import os
from typing import Iterable, Dict, Union, Tuple, Set
import numpy as np
from labels_mapper.utils import *

def change_label(seg: np.ndarray, 
                 mapping: Dict[str, int], 
                 skip: Iterable[int] = None) -> np.ndarray:
    """
    Gets a 3d array with label values. Changes them according to mapping.
    ---
    param: skip: Iterable with ints corresponding to classes that will be removed from seg
    """

    out = np.zeros_like(seg)
    for k, v in mapping.items():
        assert np.any(seg == int(k)), f'Label {k} present in json, but not in segmentation. Please revise. Corresponds to value {v}.'
        out[seg==int(k)] = int(v)
    
    if skip is not None:
        skip = list(set(skip))
        out[np.isin(out, skip)] = 0

    return out

def check_overlap(infnd: np.ndarray, supnd: np.ndarray) -> Union[None, np.ndarray]:
    """Bins two labels and checks if there is any overlap"""

    overlap = np.logical_and(infnd > 0, supnd > 0)

    if overlap.any():
        where = np.where(overlap, 1, 0)
        return where

    return 

def sum_inf_nd_sup(infnd: np.ndarray, supnd: np.ndarray, 
                   affine: np.ndarray, patient: str=None) -> np.ndarray:
    """
    Adds up both labels, from inf and sup mouth.
    """
    
    overlap = check_overlap(infnd, supnd)

    if overlap is not None:
        debugging_path = os.path.abspath(os.getcwd() + '/overlap_for_debugging.nii.gz')
        save_nifti(
            overlap,
            affine=affine,
            out_path=debugging_path,
            overwrite=True,
            dtype=np.uint8
        )
        raise RuntimeError(f'Found overlap when processing patient {patient if patient else 'UNKNOWN'}, '
                           f'saved overlap array at {debugging_path} for debugging purposes.')
    
    return infnd + supnd
    
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

def process_subject(inf_seg: np.ndarray, 
                    sup_seg: np.ndarray,
                    inf_json: Dict[str, int], 
                    sup_json: Dict[str, int], 
                    skip: Iterable[int],
                    affine: np.ndarray):

    if (inf_seg is not None) and (sup_seg is not None):
        mapped_inf = change_label(seg=inf_seg, mapping=inf_json, skip=skip)
        mapped_sup = change_label(seg=sup_seg, mapping=sup_json, skip=skip)
        summed = sum_inf_nd_sup(mapped_inf, mapped_sup, affine)
        return summed
    elif inf_seg is not None:
        mapped_inf = change_label(seg=inf_seg, mapping=inf_json, skip=skip)
        return mapped_inf
    elif sup_seg is not None:
        mapped_sup = change_label(seg=sup_seg, mapping=sup_json, skip=skip)
        return mapped_sup
    else:
        raise RuntimeError('No arguments supplied.')

def main():
    args = parse_args()

    niftis: list[str] = args.niftis
    jsons: list[str] = args.jsons
    assert len(niftis) == len(jsons), 'Different number of niftis and jsons. Please revise your arguments'
    
    out_file = args.out_file

    inf_nifti = [i for i in niftis if 'inf' in os.path.basename(i) and i.endswith('.nii.gz')]
    sup_nifti = [i for i in niftis if 'sup' in os.path.basename(i) and i.endswith('.nii.gz')]
    inf_json = [i for i in jsons if 'inf' in os.path.basename(i) and i.endswith('.json')]
    sup_json = [i for i in jsons if 'sup' in os.path.basename(i) and i.endswith('.json')]

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
        myargs['affine'] = affine
    except IndexError:
        myargs['inf_seg'] = None
        myargs['inf_json'] = None
    try:
        sup_seg, affine = load_nifti(sup_nifti[0], affine=True)
        myargs['sup_seg'] = sup_seg
        sup_json, patient = parse_json_mappings(sup_json[0], True)
        myargs['sup_json'] = sup_json
        out_path = os.path.dirname(sup_nifti[0])
        myargs['affine'] = affine
    except IndexError:
        myargs['sup_seg'] = None
        myargs['sup_json'] = None

    myargs['skip'] = args.skip

    mapped = process_subject(**myargs)

    if out_file is None:
        out_file = f'labels_mapped.nii.gz'
        out_file = os.path.join(out_path, out_file)
    
    save_nifti(
        array=mapped, 
        affine=affine,
        out_path=out_file,
        dtype=np.uint8,
        overwrite=True # maybe be user controlled?
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
    parser.add_argument('-out_file', required=False, default=None, type=str,
                        help='Output file path.')
    args, unrecognized_args = parser.parse_known_args()
    
    return args
    
if __name__ == "__main__":
    main()