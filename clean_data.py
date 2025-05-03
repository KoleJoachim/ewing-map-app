import pandas as pd

def clean_data(input_file, output_file):
    df = pd.read_csv(input_file, dtype=str)
    
    label_cols = [col for col in df.columns if '_label' in col]
    
    for col in label_cols:
        df[col] = df[col].replace({'High': 1, 'Low': 0})
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['FIPS'] = df['FIPS'].str.zfill(5).fillna("00000")
    df.to_csv(output_file, index=False)
    print(f"✅ Successfully created {output_file}")

if __name__ == "__main__":
    clean_data('final_df.csv', 'cleaned_final_data.csv')  # Fixed output name
