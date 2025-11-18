# Winding Data Converter 

Supports:
- Multiple classes (`ok`, `ng`, `ng1`, `ng2`, ...)
- Custom sampling ratios via `--data_rate`
- Balanced folder sampling per class
- HEIC → JPG conversion
- Creation of `labels.csv` and `reference.csv`

---

## Input Structure

```
winding_data/
├── 1/
│   ├── *.heic
├── 2/
│   ├── *.heic
├── ...
└── setting.csv  or setting.json
```

### Example `setting.csv`:
```csv
no,angle,distance,speed,result
1,15,1,slow,ok
2,5,1,slow,ng
3,25,1,slow,ng
4,15,3,slow,ng
5,15,1,fast,ng
```

- `no` → folder name  
- `result` → label (`ok`, `ng`, `ng1`, ...)

All `result` values are converted to lowercase automatically.

---

## Output Structure

```
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

---

## Output Files

### **1. images/**
Each sample contains **3 images**:

```
<sample_id>_a.JPG
<sample_id>_b.JPG
<sample_id>_c.JPG
```

Example:

```
1_a.JPG
1_b.JPG
1_c.JPG
```

All images in one sample are taken from **the same original folder**.

---

### **2. labels.csv**

Maps `sample_id` → numeric label ID.

Format:

```csv
sample_id,label
1,1
2,0
3,2
```

Label IDs are assigned based on **alphabetical sorting** of all unique classes:

Example:

If dataset has:

```
ok, ng1, ng2
```

Sorted order:

```
['ng1', 'ng2', 'ok']
```

Then:

```
ng1 → 0
ng2 → 1
ok  → 2
```

---

### **3. reference.csv**

Maps generated images to original HEIC files:

```csv
name,origin
1_a.JPG,20251110_025849164_iOS.heic
1_b.JPG,20251110_025856420_iOS.heic
1_c.JPG,20251110_025901004_iOS.heic
```

---

## 🔧 Requirements

Python **3.12+**

Install dependencies:

```bash
pip install -r requirements.txt
```

### requirements.txt:
```
Pillow>=10.0.0
pillow-heif
```

---

##  Usage

Basic example:

```bash
python convert_winding_data.py \
    --input ./winding_data \
    --output ./processed_data \
    --sample 10 \
    --seed 42
```

### Command-line arguments

```
--input       Path to raw winding-data directory
--output      Output directory for processed data
--sample      Number of samples to generate (each sample = 3 images)
--seed        Random seed for reproducibility
--data_rate   Class ratios (optional)
```

---

## 🎛Custom Class Ratios — `--data_rate`

Allows controlling how many samples per class.

### Example 1 — Two classes (`ok`, `ng`)
```
--data_rate 0.8,0.2
```

Console output:

```
Detected labels (order for data_rate): ng, ok
Using data_rate (normalized): 0.200, 0.800
```

Meaning:
- 20% samples → ng  
- 80% samples → ok  

---

### Example 2 — Three classes (`ok`, `ng1`, `ng2`)
```
--data_rate 0.3,0.3,0.4
```

If label order is:
```
ng1, ng2, ok
```

Then:
- 30% → ng1  
- 30% → ng2  
- 40% → ok  

---

## Sampling Logic Overview

For each sample:

1. Select class according to `--data_rate`.
2. Select folder inside class using round-robin (prevents bias).
3. Select 3 images from that folder:
   - Non-repeating until exhausted.
   - Then reshuffled and reused.
4. Convert HEIC → JPG.
5. Save as `<sample_id>_[a,b,c].JPG`.
6. Update `labels.csv` and `reference.csv`.

---

