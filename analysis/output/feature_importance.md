# Feature Importance Report

This report shows which features most influence the recommendation score (baseline applicant).

## Top features (Tree-based)

- **tuition_usd**: 0.6840
- **greV**: 0.1670
- **greQ**: 0.0608
- **cgpa**: 0.0358
- **greA**: 0.0292
- **ranking**: 0.0147
- **toefl_min**: 0.0039
- **ielts_min**: 0.0036
- **duration_years**: 0.0002
- **country_USA**: 0.0002
- **country_UK**: 0.0002
- **country_Singapore**: 0.0001
- **country_Canada**: 0.0001
- **country_Netherlands**: 0.0001
- **university_type_Public**: 0.0001
- **country_Switzerland**: 0.0000
- **country_Germany**: 0.0000

## Top features (Permutation)

- **tuition_usd**: 1.2428
- **greV**: 0.3219
- **greQ**: 0.1134
- **cgpa**: 0.0544
- **greA**: 0.0496
- **ranking**: 0.0208
- **toefl_min**: 0.0000
- **country_USA**: 0.0000
- **country_UK**: 0.0000
- **university_type_Public**: 0.0000
- **country_Canada**: 0.0000
- **country_Germany**: 0.0000
- **country_Netherlands**: 0.0000
- **country_Singapore**: -0.0000
- **duration_years**: -0.0000
- **country_Switzerland**: -0.0000
- **ielts_min**: -0.0001

## Notes and next steps
- Tree-based importances measure how much each feature reduces impurity in the forest.
- Permutation importances measure the drop in score when a feature is shuffled.
- For more granular bias analysis, run SHAP and stratified checks per country/major.
