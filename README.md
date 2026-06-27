P.E.T.R.A.---Pipeline for Experimental Transients & aRt Analysis
---
**Author**: Isaac Dean Huang

 Overview
---
This project is a modern Python port of our lab's original MATLAB processing scripts.
Originally developed to analyze transient calcium responses in DRG neurons under ultrasound stimulation, this tool automates the extraction, validation, and geometric analysis of raw fluorescence data from __MetaFluor__.  
This tool significantly improves execution speed, removes the need for expensive MATLAB licenses, and packages the entire workflow into a standalone, interactive executable that requires zero coding knowledge to run during active experiments.

The Art ANOVA analysis process can be seen in `Pipeline for Experimental Transients & aRt Analysis.ipynb` but is not yet implemented


  Respository Structure
 ---
| Code | Descrpition |  
| :--- | :--- |  
| `01_Calcium_Data_Processor.py` | Follows old MATLAB code logic |  
| `02_Advanced_Data_Processor.py` | Directly reads raw data excel file |   
| `03_Third_Data_Processor.py` | Automated region folder search & single output file /w loop |  

 `01_Calcium_Data_Processor.py` & `02_Advanced_Data_Processor.py` are older version and testing prototypes.  
 `01` follows old MATLAB pipeline where you 
1. Copy the numeric data to import_data.xlxs
2. Drag region.RGN to master experiment folder  
 
 `02` reads raw data file directly but still requires to manually drag region.RGN to master experiment folder

 

  Installation & Usage
 ---

This is the active, standalone executable for the **Calcium Imaging Data Processor**. 

This `.exe` contains the fully packaged Python pipeline used to analyze ratiometric calcium transients (340/380nm) exported from MetaFluor. **No Python installation is required to run this tool.**

### 🛠️ Features Included in this Build:
* **Auto-Detection:** Automatically finds the most recent `20*.xlsx` MetaFluor raw data file in the same folder.
* **Interactive Menu:** CLI menu to quickly select the specific experiment sheet.
* **Smart RGN Routing:** Automatically drops re-run suffixes (e.g., `-2`) to locate the correct `region.RGN` coordinates.
* **Transient Validation:** Filters physical motion artifacts using the `q_ratio` calculation and a `< 0.02` noise threshold.
* **Smart Appending:** Outputs formatted, color-coded results directly into a master `Data_Output_Simplified.xlsx` file, adding new sheets without overwriting previous runs.

### 🚀 How to Use:
1. Download the newest release from the Assets section below.
2. Place the `.exe` into your experiment folder (where your raw MetaFluor `.xlsx` and region folders are located).
   <img width="373" height="314" alt="螢幕擷取畫面 2026-06-26 112744" src="https://github.com/user-attachments/assets/48800522-476c-49ab-aa81-9f57dbfd4d98" />
3. Double-click to run!
4. Output result will be saved in Data_Output.xlsx
   <img width="960" height="516" alt="螢幕擷取畫面 2026-06-26 113029" src="https://github.com/user-attachments/assets/ed3e2f22-7f5f-4952-985e-66115f15aeba" />






