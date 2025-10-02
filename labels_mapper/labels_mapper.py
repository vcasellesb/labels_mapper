import os
import warnings
from typing import Iterable, Dict, Optional
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

def sum_inf_nd_sup(infnd: np.ndarray, supnd: np.ndarray) -> np.ndarray:
    """
    Adds up both labels, from inf and sup mouth.
    """
    overlap = np.logical_and(infnd, supnd)
    if overlap.any():
        print('*' * 20)
        print('Found overlap between inferior and superior segmentations. Gonna empty '
              'the superior area to make space for the inferior (inferior has preference).')
        print('*' * 20)
        supnd[overlap] = 0

    return infnd + supnd

def process_subject(*files: tuple[str, str],
                    skip: Optional[Iterable[int]]) -> np.ndarray:
    """
    :param files: each should be a tuple where the first item is a nifti, the second one a json
    """
    (seg_file, json_file), *files = files

    seg, affine, header = load_nifti(seg_file)

    mapping = parse_json_mappings(json_file)
    ret = change_label(seg, mapping, skip)

    for seg_file, json_file in files:
        seg, _affine, _ = load_nifti(seg_file)
        mapping = parse_json_mappings(json_file)
        if not np.allclose(affine, _affine):
            msg = (
                'Mismatch between the affines (headers) between the input segmentations given. '
                'Please proceed with caution. The observed orientations are: "%s" and "%s".' % \
                (nib.aff2axcodes(affine).__str__(), nib.aff2axcodes(_affine).__str__())
            )
            warnings.warn(msg)
        mapped_seg = change_label(seg, mapping, skip)
        ret = sum_inf_nd_sup(mapped_seg, ret)

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
    parser.add_argument('folder', type=str,
                        help="Input folder where the inf/sup segmentations and json mappings are located. "
                        "It has to be of the form either \"<subject>\", \"<subject>/labels\" or \"<subject>/labels/<rater>\".")
    parser.add_argument('-skip', required=False, default=None, nargs='+', type=int,
                        help='add after this argument the integers to skip. E.g.: 1 2 3 4')
    parser.add_argument('-o', '--out_file', type=str,
                        help='Output file path.')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()