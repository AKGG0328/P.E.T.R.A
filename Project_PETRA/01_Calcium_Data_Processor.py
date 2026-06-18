import pandas as pd
import numpy as np
import openpyxl


def load_metafluor_rgn(file_path):
    regions = []
    with open(file_path, 'r') as f:
        for line in f:
            # RGN lines are comma-separated pairs of "Tag Value"
            parts = line.strip().split(',')
            row_dict = {}
            for p in parts:
                item = p.strip().split(' ')
                if len(item) >= 2:
                    tag = item[0]
                    val = " ".join(item[1:])
                    row_dict[tag] = val
            regions.append(row_dict)

    df = pd.DataFrame(regions)
    # Tag '2' typically contains "X Y" coordinates of the top-left corner
    coords = df['2'].str.split(' ', expand=True)
    x_raw = pd.to_numeric(coords[0])
    y_raw = pd.to_numeric(coords[1].str.replace(',', '')) # Handle potential commas

    # Apply your specific scaling and Y-inversion from the MATLAB script
    df['x'] = 0.7752 * x_raw
    df['y'] = 0.7752 * (512 - y_raw)
    return df


def simple_calcium_process():
    print("\n--- Processing Simplified Calcium Imaging Data ---")

    # 1. Load Intensity Data
    try:
        original_data = pd.read_excel('import_data.xlsx', header=None).values
    except FileNotFoundError:
        print(" Error: 'import_data.xlsx' not found.")
        return

    # 2. Extract 340 and 380 Intensities
    intensity = original_data[:, [i for i in range(original_data.shape[1]) if i % 3 != 0]]
    intensity_340 = intensity[:, 0::2] - intensity[:, [0]]
    intensity_380 = intensity[:, 1::2] - intensity[:, [1]]

    # 3. Calculate Global Ratios
    with np.errstate(divide='ignore', invalid='ignore'):
        Ratio = np.where(intensity_380 != 0, intensity_340 / intensity_380, 0)
    W = Ratio.shape[1]

    # 4. Input
    print("\nEnter beginning times for US stimulation.")
    raw_input = input("Type your times separated by spaces (e.g., 60 180 300) and press Enter: ")

    us_start_list = [int(x) for x in raw_input.replace(',', ' ').split() if x.strip()]

    if not us_start_list:
        print("No time points entered. Cancelling calculation.")
        return

    # 5. Initialize the output DataFrame with the ROI/Cell numbers
    output_data = pd.DataFrame({'Number': np.arange(1, W + 1)})

    # 6. Loop through times, calculate dF/F0, and add as new columns
    for us_start in us_start_list:
        f0 = np.mean(Ratio[us_start-6 : us_start-1, :], axis=0)
        fp_window = Ratio[us_start : us_start+30, :]
        fp = np.max(fp_window, axis=0)

        with np.errstate(divide='ignore', invalid='ignore'):
            df_f0 = np.where(f0 != 0, (fp - f0) / f0, 0)

        # Append the new column to the DataFrame
        col_name = f"dF/F0_{us_start}s"
        output_data[col_name] = df_f0

        #
        peak_idx = np.argmax(fp_window, axis=0) + us_start

        # Extract intensities at peak (q0, q2) and at start (q1, q3) for every cell
        q0 = intensity_340[peak_idx, np.arange(W)]
        q2 = intensity_380[peak_idx, np.arange(W)]
        q1 = intensity_340[us_start-1, :]
        q3 = intensity_380[us_start-1, :]

        # Calculate q_ratio (340 increase * 380 decrease)
        q_ratio = (q0 - q1) * (q2 - q3)
        is_valid_transient = (q_ratio <= 0)

        # Store validation column (can be used to color formatting later)
        output_data[f"Valid_{us_start}s"] = is_valid_transient

        invalid_count = np.sum(~is_valid_transient)
        print(f"  -> Calculated: {col_name} (Found {invalid_count} rejected transients)")


    # 7. Read Region Data Directly (Ensure your custom function is defined in your environment)
    try:
        rgn_df = load_metafluor_rgn('region.RGN')
        x, y = rgn_df['x'].values, rgn_df['y'].values
    except Exception as e:
        print(f" Error loading RGN file: {e}")
        return

    # 8. Geometric Analysis (Calculated once)
    x2, y2 = x[1], y[1]
    x3, y3 = x[2], y[2]
    displacement = np.sqrt((x - x2)**2 + (y - y2)**2)

    v_line = np.array([x2 - x3, y2 - y3])
    v_cells = np.stack([x - x2, y - y2], axis=1)
    dot_product = np.dot(v_cells, v_line)
    norms = np.linalg.norm(v_line) * np.linalg.norm(v_cells, axis=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        angle_temp = np.degrees(np.arccos(np.clip(dot_product / norms, -1.0, 1.0)))

    final_angles = []
    for i in range(len(x)):
        slope_cell = (y[i] - y3) / (x[i] - x3) if (x[i] - x3) != 0 else 0
        slope_ref = v_line[1] / v_line[0] if v_line[0] != 0 else 0
        if slope_cell > slope_ref or slope_cell > 0:
            final_angles.append(360 - angle_temp[i])
        else:
            final_angles.append(angle_temp[i])

    output_data['Displacement'] = displacement
    output_data['Angle'] = final_angles

    # 9. Save to a single Excel sheet
    cols_to_drop = [col for col in output_data.columns if col.startswith('Valid_')]
    clean_data = output_data.drop(columns=cols_to_drop)

    def apply_red_labels(clean_df):
        """ Builds a style matrix using the original data as a reference """
        # Create an empty style matrix the exact same shape as the clean data
        styles = pd.DataFrame('', index=clean_df.index, columns=clean_df.columns)

        for col in clean_df.columns:
            if col.startswith('dF/F0_'):
                time_str = col.split('_')[1]
                valid_col = f"Valid_{time_str}"

                # Check the original output_data for the False flags
                if valid_col in output_data.columns:
                    invalid_mask = ~output_data[valid_col]

                    # Paint those exact coordinates red in the style matrix
                    styles.loc[invalid_mask, col] = 'background-color: #ff9999; color: black;'

        return styles

    # Apply the styling to the clean data (axis=None evaluates the whole table at once)
    styled_df = clean_data.style.apply(apply_red_labels, axis=None)

    # Save to a single Excel sheet (requires 'openpyxl')
    output_filename = 'Data_Output_Simplified.xlsx'
    styled_df.to_excel(output_filename, engine='openpyxl', index=False)
    print(f" All time points processed! Saved to '{output_filename}'\n")




simple_calcium_process()


