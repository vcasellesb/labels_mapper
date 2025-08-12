import os
import re
from typing import Iterable, Dict, Union, Set, Optional
import numpy as np
from labels_mapper.utils import *
from .folder_stuff import get_args

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

def sum_inf_nd_sup(infnd: np.ndarray,
                   supnd: np.ndarray,
                   affine: np.ndarray,
                   patient: str = None) -> np.ndarray:
    """
    Adds up both labels, from inf and sup mouth.
    """
    overlap = np.logical_and(infnd, supnd)
    if overlap.any():
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

def process_subject(*tuples: tuple[str, str],
                    skip: Optional[Iterable[int]]) -> np.ndarray:
    """
    :param tuples: should be a tuple where the first item is a nifti, the second one a json
    """
    (seg_file, json_file), *tuples = tuples

    seg, affine, header = load_nifti(seg_file)

    mapping = parse_json_mappings(json_file) 
    ret = change_label(seg, mapping, skip)
    
    for seg_file, json_file in tuples:
        seg, _affine, _ = load_nifti(seg_file)
        mapping = parse_json_mappings(json_file)
        assert np.allclose(affine, _affine)
        mapped_seg = change_label(seg, mapping, skip)
        ret += mapped_seg

    return ret, affine, header

def main():
    args = parse_args()

    folder = args.folder
    myargs = get_args(folder)

    mapped, affine, header = process_subject(*myargs, skip=args.skip)
    out_file = args.out_file
    if out_file is None:
        out_path = os.path.dirname(myargs[0][0])
        out_file = f'labels_mapped.nii.gz'
        out_file = os.path.join(out_path, out_file)

    save_nifti(
        array=mapped,
        affine=affine,
        out_path=out_file,
        header=header,
        dtype=np.uint8,
        overwrite=True # maybe be user controlled?
    )


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=str)
    parser.add_argument('-skip', required=False, default=None, nargs='+', type=int,
                        help='add after this argument the integers to skip. E.g.: 1 2 3 4')
    parser.add_argument('-o', '--out_file', type=str,
                        help='Output file path.')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()