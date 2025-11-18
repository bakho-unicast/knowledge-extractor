# Winding Data Converter

The script reads folders like:

```plaintext
winding_data/
├── 1/
│   ├── *.heic
├── 2/
│   ├── *.heic
└── setting.csv
```

Each folder number corresponds to a processing condition and contains images belonging to either OK or NG class. The result (ok/ng) must be specified in setting.csv or setting.json.

The script outputs:
```plaintext
processed_data/
├── images/
│   ├── 1_a.JPG
│   ├── 1_b.JPG
│   ├── 1_c.JPG
│   ├── 2_a.JPG
│   └── ...
├── labels.csv
└── reference.csv
```
Images are converted to JPG format using Pillow + pillow-heif.

------------------------------------------------------------
# Requirements

Python 3.12 or newer.

Install required packages:

```bash
pip install -r requirements.txt
```
------------------------------------------------------------
# Project Structure
```plaintext
project_root/
├── convert_winding_data.py
├── README.md
├── requirements.txt
└── winding_data/
    ├── 1/
    ├── 2/
    ├── ...
    └── setting.csv
```

Example setting.csv:

```csv
no,angle,distance,speed,result
1,15,1,slow,ok
2,5,1,slow,ng
3,25,1,slow,ng
4,15,3,slow,ng
5,15,1,fast,ng
```
------------------------------------------------------------
# Usage

Run the converter from the project root:

```bash
python convert_winding_data.py --input ./winding_data --output ./processed_data --sample 20 --seed 42
```
Arguments:

```plaintext
--input     Path to raw winding data directory
--output    Directory where converted data will be saved
--sample    Number of samples to generate (1 sample = 3 images)
--seed      Random seed for reproducible selection
```
------------------------------------------------------------
# Output Description

1. images/
   Contains JPG files named:
   1_a.JPG, 1_b.JPG, 1_c.JPG
   All three images of a sample come from the same folder.

2. labels.csv
   Format:
   ```csv
   sample_id,label
   1,1
   2,0
   3,1
   ```

   Label: 1 = OK, 0 = NG

4. reference.csv
   Shows mapping from generated image to the original HEIC file.

   Example:
    ```csv
   name,origin
   1_a.JPG,20251110_025849164_iOS.heic
   1_b.JPG,20251110_025856420_iOS.heic
   ```

------------------------------------------------------------


