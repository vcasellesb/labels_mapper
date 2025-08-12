#!/bin/bash

compute_on_folder () {
    folder=$1
    if [[ $(git branch --show-current) != "main" ]]; then
    git switch main
    fi
    
    python3 -m labels_mapper.labels_mapper -niftis $(ls $folder/*inf.nii.gz 2> /dev/null || ls $folder/*inf*.nii.gz) \
        $(ls $folder/*sup.nii.gz 2>/dev/null || ls $folder/*sup*.nii.gz) \
        -jsons $(ls $folder/*.json 2> /dev/null || ls $folder/json_mappings/*.json) -o $folder/result_main.nii.gz

    git switch refactor
    python3 -m labels_mapper.labels_mapper "$folder" -o $folder/result_refactor.nii.gz

    seg_stats $folder/result_main.nii.gz -d $folder/result_refactor.nii.gz
}

for folder in test-data/*/labels/R*; do
compute_on_folder $folder
done