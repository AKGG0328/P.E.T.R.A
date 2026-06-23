P.E.T.R.A.---Pipeline for Experimental Transients & aRt Analysis
---
**Author**: Isaac Dean Huang

 Overview
---
This project is a modern Python port of our lab's original MATLAB processing scripts.
Originally developed to analyze transient calcium responses in DRG neurons under ultrasound stimulation, this tool automates the extraction, validation, and geometric analysis of raw fluorescence data.  
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

 `03_Third_Data_Processor.py`  
 ### Run from source
In terminal  
1. `pip install pandas numpy openpyxl`
2. `python 03_Third_Data_Processor.py`
 
 ### Standalone Executable
1. Download the .py code
2. In terminal, `pyinstaller --onefile 03_Third_Data_Processor.py` to export to .exe file
3. Put .exe file in your master experiment folder
4. execute .exe file
5. Follow the on-screen prompts to select your target sheet and input your stimulation times.






