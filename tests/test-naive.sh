#!/bin/bash

set -e

DATA_DIR="$(pwd)/test-data"

# from: https://stackoverflow.com/a/72395091
for target in "$DATA_DIR"/*; do
    # first try running on dirs as is
    conda run -n stl2nii --live-stream bash -c "labels_mapper "$target" -o test-out/${target##*/}_from_raw.nii.gz"

    # now from dir/labels
    conda run -n stl2nii --live-stream bash -c "labels_mapper "$target"/labels -o test-out/${target##*/}_from_labels.nii.gz"

    # now for all raters
    for rater in "$target"/labels/R*; do
        conda run -n stl2nii --live-stream bash -c "labels_mapper "$rater" -o test-out/${target##*/}_from_rater_"${rater##*/}".nii.gz"
    done
done