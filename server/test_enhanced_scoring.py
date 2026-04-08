"""
Test script to verify enhanced scoring system
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from enhanced_scoring import EnhancedScorer
from university_categorizer import UniversityCategorizer
from recommendation_explainer import RecommendationExplainer
import pandas as pd
import numpy as np

print("=" * 60)
print("Testing Enhanced Scoring System")
print("=" * 60)

# Initialize components
scorer = EnhancedScorer()
categorizer = UniversityCategorizer()
explainer = RecommendationExplainer()

print("\n✓ All modules initialized successfully!\n")

# Test data - sample university
university_data = {
    'univName': 'Massachusetts Institute of Technology',
    'country': 'USA',
    'ranking': 1,
    'tuition_usd': 53790,
    'university_type': 'Private',
    'research_focused': True,
    'internship_opportunities': True,
    'post_study_work_visa': True,
    'academic_strength': 0.95,
    'ranking_score': 0.98,
    'affordability': 0.6
}

# Test user profile
user_profile = {
    'greV': 165,
    'greQ': 168,
    'greA': 4.5,
    'cgpa': 9.2,
    'ielts': 8.0,
    'major': 'Computer Science',
    'workExperience': 2,
    'publications': 1,
    'budgetMin': 40000,
    'budgetMax': 60000,
    'researchFocus': True,
    'internshipOpportunities': True,
    'workVisa': True
}

print("Test Case:")
print(f"  University: {university_data['univName']}")
print(f"  Student: GRE V:{user_profile['greV']}, Q:{user_profile['greQ']}, CGPA:{user_profile['cgpa']}")
print(f"  Budget: ${user_profile['budgetMin']:,} - ${user_profile['budgetMax']:,}")
print()

# Calculate enhanced score
uni_series = pd.Series(university_data)
final_score, score_breakdown = scorer.calculate_comprehensive_score(user_profile, uni_series)

print("Enhanced Scoring Results:")
print("-" * 60)
print(f"  Overall Score: {final_score:.3f}")
print(f"  Academic Fit: {score_breakdown['academic_fit']['score']:.1f} (Weight: 30%)")
print(f"  Admission Probability: {score_breakdown['admission_probability']['score']:.1f}% - {score_breakdown['admission_probability']['level']}")
print(f"  Financial Fit: {score_breakdown['financial_fit']['score']:.1f} (Weight: 20%)")
print(f"  Career Outcomes: {score_breakdown['career_outcomes']['score']:.1f} (Weight: 15%)")
print(f"  Personal Fit: {score_breakdown['personal_fit']['score']:.1f} (Weight: 10%)")
print()

# Get category
admission_prob = score_breakdown['admission_probability']['score'] / 100
category = categorizer.get_category(admission_prob)

print(f"University Category: {category}")
print(f"  Based on {admission_prob*100:.1f}% admission probability")
print()

# Generate explanation
explanation = explainer.generate_explanation(
    university_data['univName'],
    {
        'academic_fit': score_breakdown['academic_fit']['score'] / 100,
        'admission_probability': admission_prob,
        'financial_fit': score_breakdown['financial_fit']['score'] / 100,
        'career_outcomes': score_breakdown['career_outcomes']['score'] / 100,
        'personal_fit': score_breakdown['personal_fit']['score'] / 100
    },
    category
)

print("Explanation:")
print("-" * 60)
if explanation.get('key_strengths'):
    print("  Key Strengths:")
    for strength in explanation['key_strengths']:
        print(f"    • {strength}")
print()

if explanation.get('considerations'):
    print("  Considerations:")
    for consideration in explanation['considerations']:
        print(f"    • {consideration}")
print()

if explanation.get('admission_insight'):
    print(f"  Admission Insight: {explanation['admission_insight']}")
print()

if explanation.get('financial_insight'):
    print(f"  Financial Insight: {explanation['financial_insight']}")
print()

# Test categorization distribution
print("\n" + "=" * 60)
print("Testing University Categorization Distribution")
print("=" * 60)

test_recommendations = [
    {'admission_probability': 0.85, 'name': 'Safety University 1', 'score_breakdown': {'admission_probability': {'score': 85}}},
    {'admission_probability': 0.75, 'name': 'Safety University 2', 'score_breakdown': {'admission_probability': {'score': 75}}},
    {'admission_probability': 0.65, 'name': 'Target University 1', 'score_breakdown': {'admission_probability': {'score': 65}}},
    {'admission_probability': 0.55, 'name': 'Target University 2', 'score_breakdown': {'admission_probability': {'score': 55}}},
    {'admission_probability': 0.45, 'name': 'Reach University 1', 'score_breakdown': {'admission_probability': {'score': 45}}},
    {'admission_probability': 0.35, 'name': 'Reach University 2', 'score_breakdown': {'admission_probability': {'score': 35}}},
    {'admission_probability': 0.25, 'name': 'Long Shot University 1', 'score_breakdown': {'admission_probability': {'score': 25}}},
    {'admission_probability': 0.15, 'name': 'Long Shot University 2', 'score_breakdown': {'admission_probability': {'score': 15}}},
]

categorized = categorizer.categorize_recommendations(test_recommendations)
balanced = categorizer.get_balanced_recommendations(categorized, total_count=10)

print("\nBalanced Recommendations:")
for rec in balanced:
    prob = rec['admission_probability']
    cat = categorizer.get_category(prob)
    print(f"  {rec['name']}: {prob*100:.0f}% - {cat}")

print("\n✅ All tests passed successfully!")
print("=" * 60)
