"""
Preprocess Real_University_Data.csv to add engineered features for accurate predictions.

This script adds the following features that the recommendation algorithm requires:
1. academic_strength - Normalized weighted score from GRE and CGPA
2. ranking_score - Inverted ranking (better ranks = higher score)
3. affordability - Inverse of tuition (cheaper = more affordable)
4. research_flag - Binary flag from research_focused boolean
5. internship_flag - Binary flag from internship_opportunities boolean
"""

import pandas as pd
import numpy as np

def preprocess_university_data(input_path: str, output_path: str):
    """
    Load, clean, and engineer features for university dataset.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to save processed CSV
    """
    print(f"Loading dataset from: {input_path}")
    df = pd.read_csv(input_path)
    
    print(f"Initial shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # 1. Calculate academic_strength for each university program
    # Normalize GRE scores (range 130-170) and GPA (range 0-4.0)
    df['greV_norm'] = (df['greV'] - 130) / 40
    df['greQ_norm'] = (df['greQ'] - 130) / 40
    df['greA_norm'] = df['greA'] / 6.0
    df['cgpa_norm'] = df['cgpa'] / 4.0
    
    # Weighted academic strength: same formula as server uses
    df['academic_strength'] = (
        df['greV_norm'] * 0.25 +
        df['greQ_norm'] * 0.35 +
        df['greA_norm'] * 0.15 +
        df['cgpa_norm'] * 0.25
    )
    
    print(f"✓ Added 'academic_strength' (range: {df['academic_strength'].min():.3f} - {df['academic_strength'].max():.3f})")
    
    # 2. Calculate ranking_score (inverted ranking - lower rank number = higher score)
    # Handle missing rankings with a default poor rank
    df['ranking'] = df['ranking'].fillna(999)
    
    # Normalize ranking: top ranked (rank 1) gets score ~1.0, lower ranks get lower scores
    # Using log scale to prevent extreme differences
    max_rank = df['ranking'].max()
    df['ranking_score'] = 1 - (np.log1p(df['ranking'] - 1) / np.log1p(max_rank))
    
    # Ensure ranking_score is between 0 and 1
    df['ranking_score'] = df['ranking_score'].clip(0, 1)
    
    print(f"✓ Added 'ranking_score' (range: {df['ranking_score'].min():.3f} - {df['ranking_score'].max():.3f})")
    
    # 3. Calculate affordability (inverse of tuition - cheaper is more affordable)
    df['tuition_usd'] = df['tuition_usd'].fillna(df['tuition_usd'].median())
    
    max_tuition = df['tuition_usd'].max()
    min_tuition = df['tuition_usd'].min()
    
    # Normalize tuition and invert (high tuition = low affordability)
    df['affordability'] = 1 - ((df['tuition_usd'] - min_tuition) / (max_tuition - min_tuition))
    
    # Ensure affordability is between 0 and 1
    df['affordability'] = df['affordability'].clip(0, 1)
    
    print(f"✓ Added 'affordability' (range: {df['affordability'].min():.3f} - {df['affordability'].max():.3f})")
    
    # 4. Convert boolean flags to binary integers
    # Handle string 'True'/'False' or actual booleans
    def to_binary(series):
        """Convert True/False or 'True'/'False' to 1/0"""
        if series.dtype == bool:
            return series.astype(int)
        else:
            return series.map({'True': 1, 'False': 0, True: 1, False: 0}).fillna(0).astype(int)
    
    df['research_flag'] = to_binary(df['research_focused'])
    df['internship_flag'] = to_binary(df['internship_opportunities'])
    df['visa_flag'] = to_binary(df['post_study_work_visa'])
    
    print(f"✓ Added binary flags: research_flag, internship_flag, visa_flag")
    
    # 5. Clean and validate data
    # Remove any duplicate rows
    original_len = len(df)
    df = df.drop_duplicates()
    if len(df) < original_len:
        print(f"✓ Removed {original_len - len(df)} duplicate rows")
    
    # Handle missing values in text fields
    df['program_fields'] = df['program_fields'].fillna('')
    df['country'] = df['country'].fillna('Unknown')
    df['univName'] = df['univName'].fillna('Unknown University')
    
    # Ensure numeric fields are proper types
    numeric_cols = ['greV', 'greQ', 'greA', 'cgpa', 'ranking', 'tuition_usd', 
                    'ielts_min', 'toefl_min', 'duration_years']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop temporary normalized columns (keep only engineered features)
    temp_cols = ['greV_norm', 'greQ_norm', 'greA_norm', 'cgpa_norm']
    df = df.drop(columns=temp_cols, errors='ignore')
    
    print(f"\nFinal shape: {df.shape}")
    print(f"Final columns: {list(df.columns)}")
    
    # Save preprocessed dataset
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved preprocessed dataset to: {output_path}")
    
    # Show summary statistics for engineered features
    print("\nEngineered Features Summary:")
    print(df[['academic_strength', 'ranking_score', 'affordability', 
              'research_flag', 'internship_flag']].describe())
    
    return df

if __name__ == "__main__":
    import os
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    input_csv = os.path.join(script_dir, 'csv', 'Real_University_Data.csv')
    output_csv = os.path.join(script_dir, 'csv', 'Real_University_Data.csv')  # Overwrite original
    
    # Create backup first
    backup_csv = os.path.join(script_dir, 'csv', 'Real_University_Data_backup.csv')
    if os.path.exists(input_csv):
        import shutil
        shutil.copy(input_csv, backup_csv)
        print(f"Created backup: {backup_csv}\n")
    
    # Preprocess the data
    df = preprocess_university_data(input_csv, output_csv)
    
    print("\n" + "="*60)
    print("Preprocessing complete!")
    print("="*60)
    print(f"\nSample of preprocessed data:")
    print(df[['univName', 'country', 'academic_strength', 'ranking_score', 
              'affordability', 'research_flag']].head(10))
