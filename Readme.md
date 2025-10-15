# Labels mapper

## Usage

Once `labels_mapper` has been installed, it can be invoked as such:

```bash
python3 path/to/valid/folder -o output_file.nii.gz
```

What is meant by a valid folder? Either of the three directory depths from a folder with the following structure:

`subjXXX/labels/R[0-9]`

Where inside `subjXXX/labels/R[0-9]` the nifti (`.nii.gz`) and json files can be found. 

# Example
Let's say you want to process subject `015` segmented by rater `R5`. You could do so using either of the three following commands:
```bash
python3 015 -o 015/R5_015.nii.gz
```
or
```bash
python3 015/labels -o 015/labels/R5_015.nii.gz
```
or
```bash
python3 015/labels/R5 -o R15/labels/R5/R5_015.nii.gz
```