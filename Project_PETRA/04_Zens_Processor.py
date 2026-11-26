import os
import re
import numpy as np
import pandas as pd

def load_zeiss_xy(xy_path):
    """
    Reads Zeiss XY.csv where each region is a row.
    Row 0: column headers, Row 1: units ('µm').
    """
    df = pd.read_csv(xy_path)

    # Identify X and Y columns
    x_col = [c for c in df.columns if 'Center X' in str(c)][0]
    y_col = [c for c in df.columns if 'Center Y' in str(c)][0]

    # Skip the unit row (index 0) and extract values
    x = pd.to_numeric(df[x_col].iloc[1:], errors='coerce').dropna().values
    y = pd.to_numeric(df[y_col].iloc[1:], errors='coerce').dropna().values

    return x, y


def load_zeiss_data(csv_path):
    """
    Auto-detects and extracts all regions (R1, R2, ... RN) from data columns.
    """
    df = pd.read_csv(csv_path)
    df_numeric = df.iloc[1:].copy()

    # Discover all region numbers present in Channel1 intensity columns
    region_numbers = []
    pattern = re.compile(r'Channel1_R(\d+)_IntensityMean::')
    for c in df.columns:
        if 'Thrs' not in str(c):
            m = pattern.search(str(c))
            if m:
                region_numbers.append(int(m.group(1)))
    region_numbers = sorted(list(set(region_numbers)))

    i340_list, i380_list, ratio_list = [], [], []
    for r in region_numbers:
        col_340 = [c for c in df.columns if f'Channel1_R{r}_IntensityMean::' in str(c) and 'Thrs' not in str(c)][0]
        col_380 = [c for c in df.columns if f'Channel2_R{r}_IntensityMean::' in str(c) and 'Thrs' not in str(c)][0]
        col_ratio = [c for c in df.columns if f'Ratio_R{r}::' in str(c)][0]

        i340_list.append(pd.to_numeric(df_numeric[col_340], errors='coerce').values)
        i380_list.append(pd.to_numeric(df_numeric[col_380], errors='coerce').values)
        ratio_list.append(pd.to_numeric(df_numeric[col_ratio], errors='coerce').values)

    raw_340 = np.column_stack(i340_list)
    raw_380 = np.column_stack(i380_list)
    Ratio = np.column_stack(ratio_list)

    return raw_340, raw_380, Ratio, region_numbers


def process_zeiss_calcium():
    # 1. Detect run folders
    folders = [f for f in os.listdir('.') if os.path.isdir(f) and not f.startswith('.')]

    if not folders:
        print(" Error: No data folders found in the current directory.")
        input("Press Enter to exit...")
        return

    print("\nAvailable Data Runs:")
    for i, name in enumerate(folders):
        print(f"  [{i}] {name}")

    while True:
        choice_raw = input(
            f"\nType the number of the folder (0 to {len(folders) - 1}) or 'q' to quit: ").strip().lower()
        if choice_raw == 'q':
            return False
        try:
            choice = int(choice_raw)
            if 0 <= choice < len(folders):
                selected_folder = folders[choice]
                break
            print(" Invalid number.")
        except ValueError:
            print(" Invalid input.")

    print(f"\nProcessing folder: '{selected_folder}'...")

    # 2. Locate files
    xy_path = os.path.join(selected_folder, 'XY.csv')
    data_path = os.path.join(selected_folder, f"{selected_folder}.csv")

    if not os.path.exists(xy_path) or not os.path.exists(data_path):
        print(f" Error: Missing 'XY.csv' or '{selected_folder}.csv' inside '{selected_folder}'.")
        return

    # 3. Read Coordinates and Data
    x, y = load_zeiss_xy(xy_path)
    intensity_340, intensity_380, Ratio, region_numbers = load_zeiss_data(data_path)

    # Align counts between XY coordinates and Data columns
    total_regions = min(len(x), len(region_numbers))
    x = x[:total_regions]
    y = y[:total_regions]
    intensity_340 = intensity_340[:, :total_regions]
    intensity_380 = intensity_380[:, :total_regions]
    Ratio = Ratio[:, :total_regions]
    region_numbers = region_numbers[:total_regions]

    print(f"  -> Successfully loaded {total_regions} regions (R{region_numbers[0]} to R{region_numbers[-1]}).")

    # 4. Stimulation Time Input
    print("\nEnter beginning times (frame numbers) for US stimulation.")
    raw_input = input("Type your frame/time points separated by spaces (e.g., 60 180 300): ")
    us_start_list = [int(val) for val in raw_input.replace(',', ' ').split() if val.strip()]

    if not raw_input:
        us_start_list = [60, 180, 300, 420]
        print("  -> Using default timings: 60, 180, 300, 420")
    else:
        us_start_list = [int(val) for val in raw_input.replace(',', ' ').split() if val.strip()]

    # 5. Initialize Output DataFrame
    output_data = pd.DataFrame({'Region': [f"R{r}" for r in region_numbers]})

    # 6. Calculate dF/F0 and q_ratio validation
    W = total_regions
    for us_start in us_start_list:
        f0 = np.mean(Ratio[us_start - 6: us_start - 1, :], axis=0)
        fp_window = Ratio[us_start: us_start + 30, :]
        fp = np.max(fp_window, axis=0)

        with np.errstate(divide='ignore', invalid='ignore'):
            df_f0 = np.where(f0 != 0, (fp - f0) / f0, 0)

        col_name = f"dF/F0_{us_start}s"
        output_data[col_name] = df_f0

        peak_idx = np.argmax(fp_window, axis=0) + us_start

        q0 = intensity_340[peak_idx, np.arange(W)]
        q2 = intensity_380[peak_idx, np.arange(W)]
        q1 = intensity_340[us_start - 1, :]
        q3 = intensity_380[us_start - 1, :]

        # Transient validation: (Δ340) * (Δ380) <= 0
        q_ratio = (q0 - q1) * (q2 - q3)
        is_valid_transient = (q_ratio <= 0)

        output_data[f"Valid_{us_start}s"] = is_valid_transient
        print(f"  -> Calculated: {col_name}")

    # 7. Geometric Analysis
    # Region 2 (Waveguide tip) is at index 1
    # Region 3 (Waveguide axis) is at index 2
    x2, y2 = x[1], y[1]
    x3, y3 = x[2], y[2]

    # Displacement relative to tip (Region 2)
    displacement = np.sqrt((x - x2) ** 2 + (y - y2) ** 2)

    # Direction 2 -> 3 is defined as 180 degrees
    theta_ref = np.arctan2(y3 - y2, x3 - x2)
    theta_cells = np.arctan2(y - y2, x - x2)

    # Relative angle in degrees, normalized to [0, 360)
    final_angles = (180.0 + np.degrees(theta_cells - theta_ref)) % 360.0

    output_data['Displacement'] = displacement
    output_data['Angle'] = final_angles

    # 8. Clean validation columns for final sheet
    cols_to_drop = [col for col in output_data.columns if col.startswith('Valid_')]
    clean_data = output_data.drop(columns=cols_to_drop)

    # 9. Styling Functions
    def apply_orange_labels(df_to_style):
        """Highlights row orange if region angle is under the waveguide (135° to 225°)"""
        styles = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
        needle_mask = (df_to_style['Angle'] >= 135) & (df_to_style['Angle'] <= 225)
        styles.loc[needle_mask, :] = 'background-color: #FFAE42; color: black;'
        return styles

    def apply_red_labels(df_to_style):
        """Highlights specific dF/F0 values red if rejected or negative"""
        styles = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
        for col in df_to_style.columns:
            if col.startswith('dF/F0_'):
                time_str = col.split('_')[1]
                valid_col = f"Valid_{time_str}"
                if valid_col in output_data.columns:
                    invalid_qratio = ~output_data[valid_col]
                    threshold = df_to_style[col] >= 0.02
                    invalid_mask = invalid_qratio & threshold
                    negative_mask = df_to_style[col] < 0

                    mask = invalid_mask | negative_mask
                    styles.loc[mask, col] = 'background-color: #ff9999; color: black;'
        return styles

    styled_df = (clean_data.style
                 .apply(apply_orange_labels, axis=None)
                 .apply(apply_red_labels, axis=None))

    # 10. Save output
    output_filename = 'Data_Output.xlsx'
    sheet_name = selected_folder[:31]

    if os.path.exists(output_filename):
        with pd.ExcelWriter(output_filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            styled_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(output_filename, engine='openpyxl', mode='w') as writer:
            styled_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f" Run successfully processed and saved to sheet '{sheet_name}' in '{output_filename}'!\n")
    return True  # <--- Add this at the very end of process_zeiss_calcium()

if __name__ == "__main__":
    while True:
        keep_going = process_zeiss_calcium()
        if not keep_going:
            print("Exiting PETRA processor. Goodbye!")
            break
        print("-" * 50)