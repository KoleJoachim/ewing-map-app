import pandas as pd

def clean_data(input_file, output_file):
    df = pd.read_csv(input_file, dtype=str)
    
    # Process label columns
    label_cols = [col for col in df.columns if '_label' in col]
    for col in label_cols:
        df[col] = df[col].replace({'High': 1, 'Low': 0})
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean FIPS codes
    df['FIPS'] = df['FIPS'].str.zfill(5).fillna("00000")
    
    # Save with standardized name
    df.to_csv("cleaned_final_df.csv", index=False)
    print(f"✅ Cleaned data saved to: cleaned_final_df.csv")

if __name__ == "__main__":
    clean_data('final_df.csv', 'cleaned_final_df.csv')
