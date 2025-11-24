"""
Test script to validate match score and admission probability correlation
Tests multiple user profiles against selected universities
"""
import sys
sys.path.append('server')

from enhanced_scoring import EnhancedScorer
import pandas as pd

# Load university data
print("Loading university data...")
data = pd.read_csv('csv/Real_University_Data.csv')

# Define test profiles
test_profiles = [
    {
        "name": "High Performer (GPA 3.8, GRE 335)",
        "profile": {
            'greV': 165,
            'greQ': 170,
            'greA': 5.0,
            'cgpa': 3.8,
            'major': 'Computer Science,Engineering',
            'workExperience': 3,
            'publications': 5,
            'preferred_countries': ['USA', 'UK'],
            'budgetMin': 0,
            'budgetMax': 60000,
            'universityType': 'Any',
            'researchFocus': True,
            'internshipOpportunities': True,
            'workVisa': True
        }
    },
    {
        "name": "Medium Performer (GPA 3.2, GRE 310)",
        "profile": {
            'greV': 155,
            'greQ': 155,
            'greA': 4.0,
            'cgpa': 3.2,
            'major': 'Computer Science,Engineering',
            'workExperience': 2,
            'publications': 1,
            'preferred_countries': ['USA', 'UK'],
            'budgetMin': 0,
            'budgetMax': 60000,
            'universityType': 'Any',
            'researchFocus': False,
            'internshipOpportunities': True,
            'workVisa': True
        }
    },
    {
        "name": "Low Performer (GPA 2.8, GRE 290)",
        "profile": {
            'greV': 145,
            'greQ': 145,
            'greA': 3.0,
            'cgpa': 2.8,
            'major': 'Computer Science,Engineering',
            'workExperience': 1,
            'publications': 0,
            'preferred_countries': ['USA', 'UK'],
            'budgetMin': 0,
            'budgetMax': 60000,
            'universityType': 'Any',
            'researchFocus': False,
            'internshipOpportunities': True,
            'workVisa': True
        }
    }
]

# Test universities (select top-ranked and mid-ranked)
test_universities = ['MIT', 'Oxford University', 'University of Edinburgh', 'TUM', 'ETH Zurich']

print("\n" + "="*80)
print("VALIDATION TEST: Match Score vs Admission Probability Correlation")
print("="*80)

for test_case in test_profiles:
    print(f"\n{'='*80}")
    print(f"TEST PROFILE: {test_case['name']}")
    print(f"{'='*80}")
    print(f"GRE: V:{test_case['profile']['greV']}, Q:{test_case['profile']['greQ']}, A:{test_case['profile']['greA']}")
    print(f"GPA: {test_case['profile']['cgpa']}")
    print(f"Experience: {test_case['profile']['workExperience']} years, Publications: {test_case['profile']['publications']}")
    print(f"\n{'University':<30} {'Match':<10} {'Admission':<12} {'Status'}")
    print(f"{'-'*80}")
    
    results = []
    scorer = EnhancedScorer()
    
    for uni_name in test_universities:
        # Find university in dataset
        uni_data = data[data['univName'] == uni_name]
        if uni_data.empty:
            continue
        
        uni = uni_data.iloc[0].to_dict()
        
        # Calculate comprehensive score
        final_score, breakdown = scorer.calculate_comprehensive_score(test_case['profile'], uni)
        
        match_score = final_score  # This is already 0-100 scale
        admission_prob = breakdown['admission_probability']['score']
        admission_level = breakdown['admission_probability']['level']
        
        results.append({
            'university': uni_name,
            'match': match_score,
            'admission': admission_prob,
            'level': admission_level,
            'rank': uni.get('ranking', 999)
        })
    
    # Sort by match score descending
    results.sort(key=lambda x: x['match'], reverse=True)
    
    # Display results
    for r in results:
        print(f"{r['university']:<30} {r['match']:>6.1f}%   {r['admission']:>6.1f}%     {r['level']}")
    
    # Validation check
    print(f"\n{'Validation Check:':<30}")
    validation_passed = True
    for i in range(len(results) - 1):
        if results[i]['match'] > results[i+1]['match']:
            # Higher match score should have equal or higher admission probability
            if results[i]['admission'] < results[i+1]['admission'] - 1.0:  # Allow 1% tolerance
                print(f"  ❌ FAIL: {results[i]['university']} ({results[i]['match']:.1f}% match) has LOWER admission ({results[i]['admission']:.1f}%) than {results[i+1]['university']} ({results[i+1]['match']:.1f}% match, {results[i+1]['admission']:.1f}% admission)")
                validation_passed = False
    
    if validation_passed:
        print(f"  ✅ PASS: Match scores correlate with admission probabilities")
    
    # Calculate correlation coefficient
    if len(results) > 1:
        import numpy as np
        matches = [r['match'] for r in results]
        admissions = [r['admission'] for r in results]
        correlation = np.corrcoef(matches, admissions)[0, 1]
        print(f"  📊 Correlation coefficient: {correlation:.3f} (1.0 = perfect positive correlation)")
        if correlation < 0.5:
            print(f"     ⚠️ WARNING: Weak correlation detected (expected > 0.5)")

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("✅ All tests completed!")
print("\nExpected Behavior:")
print("  1. Higher match scores should have equal or higher admission probabilities")
print("  2. Correlation coefficient should be > 0.5 (moderate to strong positive)")
print("  3. Within same university ranking tier, better profiles get better admission chances")
print("\nNote: Some variance is expected due to:")
print("  - University selectivity (rank-based)")
print("  - GPA/GRE competitiveness relative to university standards")
print("  - Random unique variance factor (prevents identical probabilities)")
print("="*80)
