"""
Compute feature importances for the University Recommender dataset.

This script:
- Loads `csv/Real_University_Data.csv` (falls back to repo path)
- Recomputes the recommendation "Total_Score" using the same logic as the app's
  `calculate_weighted_score` (approximation) so we can train a model to predict
  the score and extract feature importances.
- Trains a RandomForestRegressor and computes both mean decrease in impurity
  (tree-based) and permutation importances.
- Writes a Markdown report and PNG plots to `analysis/output/`.

Usage:
    python analysis/feature_importance.py

Outputs:
    analysis/output/feature_importance.md
    analysis/output/feature_importance_tree.png
    analysis/output/feature_importance_permutation.png
"""
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
CSV_PATHS = [
    ROOT / 'WebScraped_data' / 'csv' / 'Real_University_Data.csv',
    ROOT / 'csv' / 'Real_University_Data.csv'
]


def load_data():
    for p in CSV_PATHS:
        if p.exists():
            print(f"Loading CSV from {p}")
            return pd.read_csv(p)
    raise FileNotFoundError(f"Real_University_Data.csv not found. Tried: {CSV_PATHS}")


def compute_total_score(df, user_profile=None):
    """
    Vectorized approximation of the app's `calculate_weighted_score`.
    If `user_profile` is None, we use a typical applicant baseline.
    Returns a Series with scores in [0,1].
    """
    # Baseline applicant if not provided
    if user_profile is None:
        user_profile = {
            'greV': 155,
            'greQ': 160,
            'greA': 4.0,
            'cgpa': 3.3,
            'ielts': np.nan,
            'toefl': np.nan,
            'country': 'Any',
            'budgetMin': 0,
            'budgetMax': 100000,
            'workExperience': 0,
            'publications': 0,
            'researchFocus': False,
            'internshipOpportunities': False,
            'workVisa': False,
            'duration': np.nan,
            'major': None,
            'universityType': 'Any',
        }

    # Academic similarity
    greV_sim = 1 - (np.abs(user_profile['greV'] - df['greV']) / 40)
    greQ_sim = 1 - (np.abs(user_profile['greQ'] - df['greQ']) / 40)
    greA_sim = 1 - (np.abs(user_profile['greA'] - df['greA']) / 6)
    cgpa_sim = 1 - (np.abs(user_profile['cgpa'] - df['cgpa']) / 4)
    academic_similarity = (greV_sim + greQ_sim + greA_sim + cgpa_sim) / 4

    # Language
    language_score = 0.5
    if not np.isnan(user_profile.get('ielts', np.nan)) and 'ielts_min' in df.columns:
        language_score = 1 - (np.abs(user_profile['ielts'] - df['ielts_min']) / 9)
    elif not np.isnan(user_profile.get('toefl', np.nan)) and 'toefl_min' in df.columns:
        language_score = 1 - (np.abs(user_profile['toefl'] - df['toefl_min']) / 120)

    # Budget & country
    country_match = np.where((df['country'].isna()) | (user_profile['country'] == 'Any'), 0.5,
                             np.where(df['country'] == user_profile['country'], 1.0, 0.3))

    budget_mid = (user_profile['budgetMin'] + user_profile['budgetMax']) / 2
    with np.errstate(divide='ignore', invalid='ignore'):
        budget_diff = np.abs(df['tuition_usd'] - budget_mid) / budget_mid
        budget_score = np.where(df['tuition_usd'].isna(), 0.5, np.maximum(0, 1 - budget_diff))

    budget_country_score = (country_match + budget_score) / 2

    # Other factors
    ranking_score = np.where(df['ranking'].isna(), 0.2, np.maximum(0, 1 - (df['ranking'] / 500)))
    other_score = ranking_score * 0.4
    other_score += np.where(user_profile.get('workExperience', 0) > 2, 0.2, 0)
    other_score += np.where(user_profile.get('publications', 0) > 0, 0.2, 0)
    other_score = np.minimum(other_score, 1.0)

    total = (academic_similarity * 0.60) + (language_score * 0.10) + ((budget_country_score / 1.0) * 0.20) + (other_score * 0.10)
    # Clip to 0-1
    return np.clip(total, 0, 1)


def prepare_features(df):
    """Select and preprocess features for modeling."""
    df = df.copy()

    # Basic numeric features we can use
    features = [
        'greV', 'greQ', 'greA', 'cgpa', 'ranking', 'tuition_usd', 'ielts_min', 'toefl_min', 'duration_years'
    ]

    # Create sensible replacements for missing numeric values
    for col in ['ranking', 'tuition_usd', 'ielts_min', 'toefl_min', 'duration_years']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # One-hot encode country and university_type (keep top countries seen in README)
    df['country'] = df['country'].fillna('Unknown')
    df = pd.get_dummies(df, columns=['country', 'university_type'], drop_first=True)

    X = df[ [c for c in features if c in df.columns] + [c for c in df.columns if c.startswith('country_') or c.startswith('university_type_')] ]
    X = X.fillna(0)
    return X


def run_analysis():
    out_dir = ROOT / 'analysis' / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_data()
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains('unnamed', case=False)]

    print(f"Dataset shape: {df.shape}")

    # Compute target score using baseline profile
    y = compute_total_score(df)

    X = prepare_features(df)

    print(f"Prepared features: {list(X.columns)}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    # Tree-based feature importances
    imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)

    # Save tree-based plot before running permutation importance (safe if perm fails)
    plt.figure(figsize=(10,6))
    imp.head(20).plot(kind='bar')
    plt.title('Tree-based feature importances')
    plt.tight_layout()
    tree_plot = out_dir / 'feature_importance_tree.png'
    plt.savefig(tree_plot)
    plt.close()

    # Permutation importances (slower) - run in try/except and fall back to single-job if parallel fails
    try:
        perm = permutation_importance(rf, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
        perm_imp = pd.Series(perm.importances_mean, index=X.columns).sort_values(ascending=False)
    except Exception as e:
        print('Permutation importance parallel run failed:', e)
        print('Falling back to single-job permutation importance (n_jobs=1, n_repeats=5)')
        try:
            perm = permutation_importance(rf, X_test, y_test, n_repeats=5, random_state=42, n_jobs=1)
            perm_imp = pd.Series(perm.importances_mean, index=X.columns).sort_values(ascending=False)
        except Exception as e2:
            print('Permutation importance fallback also failed:', e2)
            perm_imp = pd.Series([], index=[])

    # Save permutation plot if computed
    if not perm_imp.empty:
        plt.figure(figsize=(10,6))
        perm_imp.head(20).plot(kind='bar', color='C1')
        plt.title('Permutation importances (mean decrease in score)')
        plt.tight_layout()
        perm_plot = out_dir / 'feature_importance_permutation.png'
        plt.savefig(perm_plot)
        plt.close()
    else:
        perm_plot = None

    # Write markdown report
    report = out_dir / 'feature_importance.md'
    with open(report, 'w', encoding='utf-8') as fh:
        fh.write('# Feature Importance Report\n\n')
        fh.write('This report shows which features most influence the recommendation score (baseline applicant).\n\n')
        fh.write('## Top features (Tree-based)\n\n')
        for f, v in imp.head(20).items():
            fh.write(f'- **{f}**: {v:.4f}\n')
        fh.write('\n## Top features (Permutation)\n\n')
        for f, v in perm_imp.head(20).items():
            fh.write(f'- **{f}**: {v:.4f}\n')
        fh.write('\n## Notes and next steps\n')
        fh.write('- Tree-based importances measure how much each feature reduces impurity in the forest.\n')
        fh.write('- Permutation importances measure the drop in score when a feature is shuffled.\n')
        fh.write('- For more granular bias analysis, run SHAP and stratified checks per country/major.\n')

    # Also save JSON summary
    summary = {
        'tree_importances': imp.head(50).round(6).to_dict(),
        'permutation_importances': perm_imp.head(50).round(6).to_dict(),
        'features': list(X.columns)
    }
    with open(out_dir / 'feature_importance_summary.json', 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)

    print('Analysis complete. Outputs saved to', out_dir)


if __name__ == '__main__':
    run_analysis()
