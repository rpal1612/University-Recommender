import random
from flask import Flask, render_template, request, redirect
from markupsafe import escape
import pandas as pd
import numpy as np
import csv
import math
from sklearn import neighbors, datasets
from numpy.random import permutation
from sklearn.metrics import precision_recall_fscore_support
app = Flask(__name__, static_folder='../static/dist', template_folder='../static')

# Load and prepare enhanced data once at startup for better performance
print("Loading and preparing enhanced university data...")
import os
csv_path = os.path.join(os.path.dirname(__file__), '..', 'WebScraped_data', 'csv', 'Enhanced_University_Data.csv')
data = pd.read_csv(csv_path)
data.drop(data.columns[data.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)

print(f"Loaded {len(data)} universities with columns: {list(data.columns)}")

# Create score-based segments for faster searching
def create_data_segments(df):
    segments = {}
    
    # Create segments based on total GRE score ranges
    df['total_gre'] = df['greV'] + df['greQ']
    
    # Define score ranges
    ranges = [
        (260, 290, 'low'),      # Very low scores
        (290, 310, 'below_avg'), # Below average
        (310, 320, 'average'),   # Average
        (320, 330, 'above_avg'), # Above average  
        (330, 340, 'high'),      # High scores
        (340, 400, 'excellent')  # Excellent scores
    ]
    
    for min_score, max_score, segment_name in ranges:
        mask = (df['total_gre'] >= min_score) & (df['total_gre'] < max_score)
        segments[segment_name] = df[mask].copy()
        print(f"Segment '{segment_name}' ({min_score}-{max_score}): {len(segments[segment_name])} universities")
    
    return segments

# Create segments at startup
data_segments = create_data_segments(data)
print("Data segmentation complete!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graduate')
def graduate():
    return render_template('graduate.html')

@app.route("/main")
def return_main():
    return render_template('index.html')

# Removed undergraduate route - focusing only on graduate recommendations

def get_appropriate_segment(greV, greQ, cgpa):
    """Select the appropriate data segment based on GRE scores"""
    total_gre = greV + greQ
    
    if total_gre < 290:
        return 'low'
    elif total_gre < 310:
        return 'below_avg'
    elif total_gre < 320:
        return 'average'
    elif total_gre < 330:
        return 'above_avg'
    elif total_gre < 340:
        return 'high'
    else:
        return 'excellent'

def euclidean_dist(test, train, length):
    distance = 0
    # test is a DataFrame with one row, train is a Series
    # We only want to compare the first 'length' columns (greV, greQ, greA, cgpa)
    for x in range(length):
        test_val = test.iloc[0, x]
        train_val = train.iloc[x]
        distance += np.square(test_val - train_val)
    return np.sqrt(distance)

def filter_universities(df, user_prefs):
    """
    Apply hard filters based on user preferences
    Returns filtered DataFrame
    """
    filtered_df = df.copy()
    initial_count = len(filtered_df)
    
    # Country filter
    if user_prefs.get('country') and user_prefs['country'] != 'Any':
        filtered_df = filtered_df[filtered_df['country'] == user_prefs['country']]
        print(f"After country filter ({user_prefs['country']}): {len(filtered_df)} universities")
    
    # Budget filter (tuition within range)
    if user_prefs.get('budgetMin') and user_prefs.get('budgetMax'):
        # Keep universities where tuition is within budget OR tuition is NaN (unknown)
        filtered_df = filtered_df[
            (filtered_df['tuition_usd'].isna()) | 
            ((filtered_df['tuition_usd'] >= user_prefs['budgetMin']) & 
             (filtered_df['tuition_usd'] <= user_prefs['budgetMax']))
        ]
        print(f"After budget filter (${user_prefs['budgetMin']}-${user_prefs['budgetMax']}): {len(filtered_df)} universities")
    
    # University type filter
    if user_prefs.get('universityType') and user_prefs['universityType'] != 'Any':
        filtered_df = filtered_df[
            (filtered_df['university_type'] == user_prefs['universityType']) |
            (filtered_df['university_type'].isna())
        ]
        print(f"After type filter ({user_prefs['universityType']}): {len(filtered_df)} universities")
    
    # Ranking filter
    if user_prefs.get('rankingMax'):
        filtered_df = filtered_df[
            (filtered_df['ranking'].isna()) |
            (filtered_df['ranking'] <= user_prefs['rankingMax'])
        ]
        print(f"After ranking filter (≤{user_prefs['rankingMax']}): {len(filtered_df)} universities")
    
    # Duration filter
    if user_prefs.get('duration') and user_prefs['duration'] < 2:
        filtered_df = filtered_df[
            (filtered_df['duration_years'].isna()) |
            (filtered_df['duration_years'] == user_prefs['duration'])
        ]
        print(f"After duration filter ({user_prefs['duration']} year): {len(filtered_df)} universities")
    
    # Field of study filter
    if user_prefs.get('major'):
        # Check if the major is in the program_fields (stored as comma-separated)
        filtered_df = filtered_df[
            (filtered_df['program_fields'].isna()) |
            (filtered_df['program_fields'].str.contains(user_prefs['major'], case=False, na=False))
        ]
        print(f"After field filter ({user_prefs['major']}): {len(filtered_df)} universities")
    
    # Boolean preference filters (research, internship, work visa)
    if user_prefs.get('researchFocus'):
        filtered_df = filtered_df[
            (filtered_df['research_focused'].isna()) |
            (filtered_df['research_focused'] == True)
        ]
        print(f"After research filter: {len(filtered_df)} universities")
    
    if user_prefs.get('internshipOpportunities'):
        filtered_df = filtered_df[
            (filtered_df['internship_opportunities'].isna()) |
            (filtered_df['internship_opportunities'] == True)
        ]
        print(f"After internship filter: {len(filtered_df)} universities")
    
    if user_prefs.get('workVisa'):
        filtered_df = filtered_df[
            (filtered_df['post_study_work_visa'].isna()) |
            (filtered_df['post_study_work_visa'] == True)
        ]
        print(f"After work visa filter: {len(filtered_df)} universities")
    
    # Language proficiency filter (IELTS/TOEFL)
    if user_prefs.get('ielts'):
        filtered_df = filtered_df[
            (filtered_df['ielts_min'].isna()) |
            (filtered_df['ielts_min'] <= user_prefs['ielts'])
        ]
        print(f"After IELTS filter (≥{user_prefs['ielts']}): {len(filtered_df)} universities")
    
    if user_prefs.get('toefl'):
        filtered_df = filtered_df[
            (filtered_df['toefl_min'].isna()) |
            (filtered_df['toefl_min'] <= user_prefs['toefl'])
        ]
        print(f"After TOEFL filter (≥{user_prefs['toefl']}): {len(filtered_df)} universities")
    
    print(f"Total filtered: {initial_count} → {len(filtered_df)} universities")
    return filtered_df

def calculate_weighted_score(user_data, uni_row):
    """
    Calculate weighted similarity score
    Weights: GRE/GPA (60%), Language (10%), Budget/Country (20%), Others (10%)
    """
    score = 0
    
    # 1. Academic scores (60% weight)
    gre_verbal_diff = abs(user_data['greV'] - uni_row['greV']) / 40  # Normalize by range
    gre_quant_diff = abs(user_data['greQ'] - uni_row['greQ']) / 40
    gre_writing_diff = abs(user_data['greA'] - uni_row['greA']) / 6
    cgpa_diff = abs(user_data['cgpa'] - uni_row['cgpa']) / 4
    
    academic_similarity = 1 - ((gre_verbal_diff + gre_quant_diff + gre_writing_diff + cgpa_diff) / 4)
    score += academic_similarity * 0.60
    
    # 2. Language proficiency (10% weight)
    language_score = 0
    if user_data.get('ielts') and not pd.isna(uni_row['ielts_min']):
        language_diff = abs(user_data['ielts'] - uni_row['ielts_min']) / 9
        language_score = 1 - language_diff
    elif user_data.get('toefl') and not pd.isna(uni_row['toefl_min']):
        language_diff = abs(user_data['toefl'] - uni_row['toefl_min']) / 120
        language_score = 1 - language_diff
    else:
        language_score = 0.5  # Neutral if no data
    score += language_score * 0.10
    
    # 3. Budget and Country match (20% weight)
    budget_country_score = 0
    
    # Country match (10%)
    if user_data.get('country') == 'Any' or pd.isna(uni_row['country']):
        budget_country_score += 0.5
    elif user_data.get('country') == uni_row['country']:
        budget_country_score += 1.0
    else:
        budget_country_score += 0.3  # Partial credit for different country
    
    # Budget match (10%)
    if pd.isna(uni_row['tuition_usd']):
        budget_country_score += 0.5
    else:
        budget_mid = (user_data['budgetMin'] + user_data['budgetMax']) / 2
        budget_diff = abs(uni_row['tuition_usd'] - budget_mid) / budget_mid
        budget_country_score += max(0, 1 - budget_diff)
    
    score += (budget_country_score / 2) * 0.20
    
    # 4. Other factors (10% weight) - ranking, duration, preferences
    other_score = 0
    
    # Ranking bonus
    if not pd.isna(uni_row['ranking']):
        # Lower ranking number is better (normalize to 0-1 scale)
        ranking_score = max(0, 1 - (uni_row['ranking'] / 500))
        other_score += ranking_score * 0.4
    else:
        other_score += 0.2
    
    # Work experience and publications give slight boost
    if user_data.get('workExperience', 0) > 2:
        other_score += 0.2
    if user_data.get('publications', 0) > 0:
        other_score += 0.2
    
    # Preference matches
    if user_data.get('researchFocus') and uni_row.get('research_focused'):
        other_score += 0.1
    if user_data.get('internshipOpportunities') and uni_row.get('internship_opportunities'):
        other_score += 0.1
    
    score += min(other_score, 1.0) * 0.10
    
    return score

def optimized_knn(greV, greQ, greA, cgpa, user_prefs={}, k=7):
    """Optimized KNN with filtering and weighted scoring"""
    
    # Get the appropriate segment
    segment_name = get_appropriate_segment(greV, greQ, user_prefs.get('cgpa', cgpa))
    trainSet = data_segments[segment_name]
    
    # Apply filters first
    filtered_trainSet = filter_universities(trainSet, user_prefs)
    
    # If filtered set is too small, expand to adjacent segments
    if len(filtered_trainSet) < k * 2:
        print(f"Filtered segment too small ({len(filtered_trainSet)} records), expanding search...")
        # Combine with adjacent segments
        all_segments = ['low', 'below_avg', 'average', 'above_avg', 'high', 'excellent']
        current_idx = all_segments.index(segment_name)
        
        combined_data = [filtered_trainSet]
        # Add adjacent segments with filtering
        if current_idx > 0:
            combined_data.append(filter_universities(data_segments[all_segments[current_idx - 1]], user_prefs))
        if current_idx < len(all_segments) - 1:
            combined_data.append(filter_universities(data_segments[all_segments[current_idx + 1]], user_prefs))
            
        filtered_trainSet = pd.concat(combined_data, ignore_index=True)
    
    # If still too small, use unfiltered data
    if len(filtered_trainSet) < k:
        print(f"Warning: Only {len(filtered_trainSet)} universities match all criteria, using broader search")
        filtered_trainSet = trainSet
    
    print(f"Processing {len(filtered_trainSet)} universities from segment '{segment_name}'")
    
    # Prepare user data for weighted scoring
    user_data = {
        'greV': greV,
        'greQ': greQ,
        'greA': greA,
        'cgpa': cgpa,
        **user_prefs
    }
    
    # Calculate weighted scores for all universities
    scores = {}
    for idx in range(len(filtered_trainSet)):
        row = filtered_trainSet.iloc[idx]
        weighted_score = calculate_weighted_score(user_data, row)
        scores[idx] = weighted_score
    
    # Sort by weighted score (higher is better, so we want descending order)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(f"Found {len(sorted_scores)} matches, top 5 scores: {sorted_scores[:5]}")

    # Get unique universities - keep expanding until we have at least 5 unique ones
    seen_universities = set()
    unique_recommendations = []
    neighbors_list = []
    
    for idx, score in sorted_scores:
        uni_name = filtered_trainSet.iloc[idx]['univName']
        
        if uni_name not in seen_universities:
            seen_universities.add(uni_name)
            unique_recommendations.append((uni_name, score))
            neighbors_list.append(idx)
            
            if len(unique_recommendations) >= 5:
                break
    
    print(f"Selected {len(unique_recommendations)} unique universities")
    
    # Format as expected by the rest of the code (university_name, count)
    # Since we want unique universities, count is always 1
    sortedNeighbors = [(uni_name, 1) for uni_name, score in unique_recommendations]
    
    return sortedNeighbors, neighbors_list, filtered_trainSet





# Undergraduate functionality removed - focusing only on graduate recommendations

  
@app.route('/graduatealgo')
def graduatealgo():
    try:
        # Get basic academic scores
        greV = float(request.args.get("greV"))
        greQ = float(request.args.get("greQ"))
        greA = float(request.args.get("greA")) 
        cgpa = float(request.args.get("cgpa"))
        
        # Get language proficiency
        englishTest = request.args.get("englishTest", "None")
        ielts = float(request.args.get("ielts", 0)) if request.args.get("ielts") else None
        toefl = float(request.args.get("toefl", 0)) if request.args.get("toefl") else None
        
        # Get academic background
        major = request.args.get("major", "")
        
        # Get professional experience
        workExperience = float(request.args.get("workExperience", 0))
        publications = int(request.args.get("publications", 0))
        
        # Get preferences
        country = request.args.get("country", "Any")
        budgetMin = float(request.args.get("budgetMin", 0))
        budgetMax = float(request.args.get("budgetMax", 100000))
        universityType = request.args.get("universityType", "Any")
        rankingMax = int(request.args.get("rankingMax", 1000))
        duration = int(request.args.get("duration", 2))
        
        # Get boolean preferences
        researchFocus = request.args.get("researchFocus") == "true"
        internshipOpportunities = request.args.get("internshipOpportunities") == "true"
        workVisa = request.args.get("workVisa") == "true"
        
        print(f"Processing comprehensive request:")
        print(f"  Academic: GRE V:{greV}, Q:{greQ}, A:{greA}, GPA:{cgpa}")
        print(f"  Language: {englishTest} - IELTS:{ielts}, TOEFL:{toefl}")
        print(f"  Background: Major:{major}, Experience:{workExperience}y, Publications:{publications}")
        print(f"  Preferences: Country:{country}, Budget:${budgetMin}-${budgetMax}, Type:{universityType}")
        print(f"  Filters: Ranking≤{rankingMax}, Duration:{duration}y, Research:{researchFocus}, Internship:{internshipOpportunities}, Visa:{workVisa}")
        
        # Build user preferences dictionary
        user_prefs = {
            'cgpa': cgpa,
            'country': country,
            'budgetMin': budgetMin,
            'budgetMax': budgetMax,
            'universityType': universityType,
            'rankingMax': rankingMax,
            'duration': duration,
            'major': major,
            'workExperience': workExperience,
            'publications': publications,
            'researchFocus': researchFocus,
            'internshipOpportunities': internshipOpportunities,
            'workVisa': workVisa
        }
        
        # Add language scores if provided
        if ielts:
            user_prefs['ielts'] = ielts
        if toefl:
            user_prefs['toefl'] = toefl
        
        # Use optimized KNN algorithm with filtering
        result, neigh, filtered_data = optimized_knn(greV, greQ, greA, cgpa, user_prefs, k=7)
        
        list1 = []
        list2 = []
        for i in result:
            list1.append(i[0])
        for i in result:
            list2.append(i[1])
        
        # Ensure we have at least 5 results
        while len(list1) < 5:
            list1.append("No additional recommendations available")
            list2.append(0)
        
        # Get university details for display
        uni_details = []
        for uni_name in list1[:5]:
            if uni_name != "No additional recommendations available":
                uni_info = filtered_data[filtered_data['univName'] == uni_name].iloc[0]
                details = {
                    'name': uni_name,
                    'country': uni_info.get('country', 'N/A'),
                    'ranking': int(uni_info['ranking']) if not pd.isna(uni_info.get('ranking')) else 'N/A',
                    'tuition': f"${int(uni_info['tuition_usd']):,}" if not pd.isna(uni_info.get('tuition_usd')) else 'Contact University',
                    'type': uni_info.get('university_type', 'N/A'),
                    'duration': f"{int(uni_info['duration_years'])} year{'s' if uni_info['duration_years'] > 1 else ''}" if not pd.isna(uni_info.get('duration_years')) else 'N/A',
                    'ielts': uni_info['ielts_min'] if not pd.isna(uni_info.get('ielts_min')) else 'N/A',
                    'toefl': uni_info['toefl_min'] if not pd.isna(uni_info.get('toefl_min')) else 'N/A',
                }
                uni_details.append(details)
            else:
                uni_details.append(None)
        
        for detail in uni_details:
            if detail:
                print(f"Recommended: {detail['name']} ({detail['country']}) - Rank: {detail['ranking']}")
        
        return f'''
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Your University Recommendations</title>
                    
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
                    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                    <!-- UI Version 3.0 - Modern Card Design - Updated: 2025-10-18 21:45 -->
                    <style>
                        * {{
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }}
                        
                        body {{
                            font-family: 'Poppins', sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            padding: 40px 20px;
                        }}
                        
                        .navbar {{
                            background: rgba(0, 0, 0, 0.8) !important;
                            backdrop-filter: blur(10px);
                            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
                            border-radius: 15px;
                            padding: 15px 20px;
                            margin-bottom: 30px;
                        }}
                        
                        .navbar-brand {{
                            font-weight: 700;
                            font-size: 1.5rem;
                            color: #fff !important;
                            display: flex;
                            align-items: center;
                            gap: 10px;
                        }}
                        
                        .navbar-brand i {{
                            color: #ffd700;
                        }}
                        
                        .nav-link {{
                            color: #fff !important;
                            font-weight: 500;
                            transition: all 0.3s ease;
                            padding: 8px 15px;
                            border-radius: 8px;
                            margin: 0 5px;
                        }}
                        
                        .nav-link:hover {{
                            background: rgba(255, 255, 255, 0.1);
                            transform: translateY(-2px);
                        }}
                        
                        .nav-link.active {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        
                        .results-container {{
                            background: rgba(255, 255, 255, 0.95);
                            backdrop-filter: blur(10px);
                            border-radius: 25px;
                            padding: 50px;
                            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                            animation: fadeInUp 0.8s ease;
                            max-width: 1100px;
                            margin: 20px auto;
                        }}
                        
                        @keyframes fadeInUp {{
                            from {{
                                opacity: 0;
                                transform: translateY(30px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateY(0);
                            }}
                        }}
                        
                        .results-container h1 {{
                            font-size: 3.2rem;
                            font-weight: 700;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                            margin-bottom: 15px;
                            text-align: center;
                            animation: titleSlide 0.8s ease;
                        }}
                        
                        @keyframes titleSlide {{
                            from {{
                                opacity: 0;
                                transform: translateY(-20px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateY(0);
                            }}
                        }}
                        
                        .results-container h1 i {{
                            color: #ffd700;
                            animation: trophySpin 3s infinite;
                        }}
                        
                        @keyframes trophySpin {{
                            0%, 100% {{ transform: rotate(0deg); }}
                            25% {{ transform: rotate(-10deg); }}
                            75% {{ transform: rotate(10deg); }}
                        }}
                        
                        .results-container > p {{
                            text-align: center;
                            color: #555;
                            margin-bottom: 20px;
                            font-size: 1.15rem;
                            font-weight: 400;
                            line-height: 1.6;
                        }}
                        
                        .score-summary {{
                            background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                            padding: 30px;
                            border-radius: 20px;
                            margin: 40px 0;
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                            gap: 25px;
                            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.1);
                            border: 2px solid rgba(102, 126, 234, 0.1);
                        }}
                        
                        .score-item {{
                            text-align: center;
                            padding: 20px;
                            background: white;
                            border-radius: 15px;
                            transition: all 0.3s ease;
                            border: 2px solid rgba(102, 126, 234, 0.05);
                        }}
                        
                        .score-item:hover {{
                            transform: translateY(-5px);
                            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.15);
                            border-color: rgba(102, 126, 234, 0.2);
                        }}
                        
                        .score-item .label {{
                            font-size: 0.95rem;
                            color: #666;
                            margin-bottom: 10px;
                            font-weight: 500;
                        }}
                        
                        .score-item .label i {{
                            color: #667eea;
                            margin-right: 5px;
                        }}
                        
                        .score-item .value {{
                            font-size: 2.2rem;
                            font-weight: 700;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                        }}
                        
                        .recommendation-card {{
                            background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%);
                            border-radius: 20px;
                            padding: 35px;
                            margin-bottom: 30px;
                            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.15);
                            border: 2px solid rgba(102, 126, 234, 0.1);
                            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            animation: slideIn 0.6s ease;
                            animation-fill-mode: backwards;
                            position: relative;
                            overflow: hidden;
                        }}
                        
                        .recommendation-card::before {{
                            content: '';
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 6px;
                            height: 100%;
                            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
                        }}
                        
                        .recommendation-card:nth-child(1) {{ animation-delay: 0.1s; }}
                        .recommendation-card:nth-child(2) {{ animation-delay: 0.2s; }}
                        .recommendation-card:nth-child(3) {{ animation-delay: 0.3s; }}
                        .recommendation-card:nth-child(4) {{ animation-delay: 0.4s; }}
                        .recommendation-card:nth-child(5) {{ animation-delay: 0.5s; }}
                        
                        @keyframes slideIn {{
                            from {{
                                opacity: 0;
                                transform: translateX(-20px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateX(0);
                            }}
                        }}
                        
                        .recommendation-card:hover {{
                            transform: translateY(-8px) scale(1.02);
                            box-shadow: 0 20px 60px rgba(102, 126, 234, 0.25);
                            border-color: rgba(102, 126, 234, 0.3);
                        }}
                        
                        .recommendation-card .rank {{
                            position: absolute;
                            top: 25px;
                            left: 25px;
                            width: 70px;
                            height: 70px;
                            line-height: 70px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border-radius: 50%;
                            text-align: center;
                            font-weight: 700;
                            font-size: 1.8rem;
                            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4), 0 0 40px rgba(102, 126, 234, 0.2);
                            animation: rankPulse 2s infinite;
                            z-index: 10;
                        }}
                        
                        @keyframes rankPulse {{
                            0%, 100% {{ box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4), 0 0 40px rgba(102, 126, 234, 0.2); }}
                            50% {{ box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6), 0 0 50px rgba(102, 126, 234, 0.3); }}
                        }}
                        
                        .recommendation-card .university-name {{
                            font-size: 1.8rem;
                            font-weight: 700;
                            color: #1a1a2e;
                            margin-bottom: 25px;
                            padding-left: 110px;
                            padding-top: 5px;
                            line-height: 1.3;
                            min-height: 70px;
                            display: flex;
                            align-items: center;
                        }}
                        
                        .recommendation-card .university-name i {{
                            color: #667eea;
                            margin-right: 8px;
                        }}
                        
                        .google-search-link {{
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            width: 35px;
                            height: 35px;
                            margin-left: 12px;
                            background: linear-gradient(135deg, #4285f4 0%, #34a853 50%, #fbbc05 75%, #ea4335 100%);
                            border-radius: 50%;
                            text-decoration: none;
                            transition: all 0.3s ease;
                            box-shadow: 0 3px 10px rgba(66, 133, 244, 0.3);
                        }}
                        
                        .google-search-link:hover {{
                            transform: scale(1.15) rotate(5deg);
                            box-shadow: 0 5px 20px rgba(66, 133, 244, 0.5);
                        }}
                        
                        .google-search-link i {{
                            color: white !important;
                            font-size: 0.9rem;
                            margin: 0 !important;
                        }}
                        
                        .recommendation-card .match-score {{
                            font-size: 1rem;
                            color: #555;
                            line-height: 1.8;
                        }}
                        
                        .recommendation-card .match-score strong {{
                            color: #667eea;
                            font-weight: 700;
                        }}
                        
                        .info-grid {{
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                            gap: 15px;
                            margin-top: 20px;
                        }}
                        
                        .info-item {{
                            background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
                            padding: 15px 20px;
                            border-radius: 12px;
                            font-size: 1rem;
                            font-weight: 500;
                            border: 1px solid rgba(102, 126, 234, 0.1);
                            transition: all 0.3s ease;
                            display: flex;
                            align-items: center;
                            gap: 10px;
                        }}
                        
                        .info-item:hover {{
                            background: linear-gradient(135deg, #e8eeff 0%, #dde6ff 100%);
                            transform: translateY(-2px);
                            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.15);
                        }}
                        
                        .info-item i {{
                            color: #667eea;
                            font-size: 1.2rem;
                            min-width: 24px;
                            text-align: center;
                        }}
                        
                        .info-item strong {{
                            color: #667eea;
                            margin-right: 5px;
                        }}
                        
                        .section-heading {{
                            text-align: center;
                            color: #1a1a2e;
                            font-size: 2rem;
                            font-weight: 700;
                            margin: 50px 0 40px 0;
                            position: relative;
                            padding-bottom: 20px;
                        }}
                        
                        .section-heading::after {{
                            content: '';
                            position: absolute;
                            bottom: 0;
                            left: 50%;
                            transform: translateX(-50%);
                            width: 120px;
                            height: 5px;
                            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                            border-radius: 3px;
                            box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                        }}
                        
                        .section-heading i {{
                            color: #ffd700;
                            margin-right: 12px;
                            animation: starTwinkle 2s infinite;
                        }}
                        
                        @keyframes starTwinkle {{
                            0%, 100% {{ opacity: 1; transform: scale(1); }}
                            50% {{ opacity: 0.7; transform: scale(1.1); }}
                        }}
                        
                        .action-buttons {{
                            display: flex;
                            gap: 15px;
                            justify-content: center;
                            margin-top: 40px;
                            flex-wrap: wrap;
                        }}
                        
                        .btn-custom {{
                            padding: 15px 35px;
                            border-radius: 50px;
                            font-weight: 600;
                            font-size: 1.05rem;
                            text-decoration: none;
                            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            display: inline-flex;
                            align-items: center;
                            gap: 12px;
                            position: relative;
                            overflow: hidden;
                        }}
                        
                        .btn-primary-custom {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                        }}
                        
                        .btn-primary-custom::before {{
                            content: '';
                            position: absolute;
                            top: 0;
                            left: -100%;
                            width: 100%;
                            height: 100%;
                            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                            transition: left 0.4s ease;
                            z-index: 0;
                        }}
                        
                        .btn-primary-custom:hover::before {{
                            left: 0;
                        }}
                        
                        .btn-primary-custom:hover {{
                            transform: translateY(-3px) scale(1.05);
                            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                            color: white;
                        }}
                        
                        .btn-primary-custom i,
                        .btn-primary-custom span {{
                            position: relative;
                            z-index: 1;
                        }}
                        
                        .btn-secondary-custom {{
                            background: white;
                            color: #667eea;
                            border: 3px solid #667eea;
                            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
                        }}
                        
                        .btn-secondary-custom:hover {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border-color: transparent;
                            transform: translateY(-3px) scale(1.05);
                            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                        }}
                        
                        .recommendations-list {{
                            animation: fadeIn 1s ease;
                        }}
                        
                        @keyframes fadeIn {{
                            from {{ opacity: 0; }}
                            to {{ opacity: 1; }}
                        }}
                        
                        @media (max-width: 768px) {{
                            .results-container {{
                                padding: 30px 20px;
                            }}
                            
                            .results-container h1 {{
                                font-size: 2rem;
                            }}
                            
                            .score-summary {{
                                grid-template-columns: repeat(2, 1fr);
                                gap: 15px;
                                padding: 20px;
                            }}
                            
                            .info-grid {{
                                grid-template-columns: 1fr;
                            }}
                            
                            .recommendation-card {{
                                padding: 25px 20px;
                            }}
                            
                            .recommendation-card .rank {{
                                width: 50px;
                                height: 50px;
                                line-height: 50px;
                                font-size: 1.3rem;
                                top: 20px;
                                left: 20px;
                            }}
                            
                            .recommendation-card .university-name {{
                                font-size: 1.2rem;
                                padding-left: 80px;
                                min-height: 50px;
                            }}
                            
                            .section-heading {{
                                font-size: 1.5rem;
                            }}
                            
                            .btn-custom {{
                                padding: 12px 25px;
                                font-size: 0.95rem;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <nav class="navbar navbar-expand-md navbar-dark">
                            <h3 class="navbar-brand">
                                <i class="fas fa-graduation-cap"></i>
                                Graduate University Finder
                            </h3>
                            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarsExample05" aria-controls="navbarsExample05" aria-expanded="false" aria-label="Toggle navigation">
                                <span class="navbar-toggler-icon"></span>
                            </button>
                            <div class="collapse navbar-collapse" id="navbarsExample05">
                                <ul class="navbar-nav ml-auto">
                                    <li class="nav-item">
                                        <a class="nav-link" href="/main"><i class="fas fa-home"></i> Home</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="/graduate"><i class="fas fa-search"></i> Find Universities</a>
                                    </li>
                                </ul>
                            </div>
                        </nav>
                    </div>

                    <div class="container">
                        <div class="results-container">
                            <h1><i class="fas fa-trophy"></i> Your Perfect Matches!</h1>
                            <p>Based on your academic profile and preferences, here are the top universities matched just for you</p>
                            
                            <div class="score-summary">
                                <div class="score-item">
                                    <div class="label"><i class="fas fa-pen"></i> GRE Verbal</div>
                                    <div class="value">{greV}</div>
                                </div>
                                <div class="score-item">
                                    <div class="label"><i class="fas fa-calculator"></i> GRE Quant</div>
                                    <div class="value">{greQ}</div>
                                </div>
                                <div class="score-item">
                                    <div class="label"><i class="fas fa-pen-fancy"></i> GRE Writing</div>
                                    <div class="value">{greA}</div>
                                </div>
                                <div class="score-item">
                                    <div class="label"><i class="fas fa-award"></i> GPA</div>
                                    <div class="value">{cgpa}</div>
                                </div>
                            </div>
                            
                            <h3 class="section-heading">
                                <i class="fas fa-star"></i> Top 5 Recommended Universities
                            </h3>
                            
                            <div class="recommendations-list">
                                ''' + ''.join([f'''
                                <div class="recommendation-card">
                                    <div class="rank">{i+1}</div>
                                    <div class="university-name">
                                        <div>
                                            <i class="fas fa-university"></i> {detail['name'] if detail else list1[i]}
                                            <a href="https://www.google.com/search?q={(detail['name'] if detail else list1[i]).replace(' ', '+')}" 
                                               target="_blank" 
                                               class="google-search-link" 
                                               title="Search on Google">
                                                <i class="fab fa-google"></i>
                                            </a>
                                        </div>
                                    </div>
                                    {f"""
                                    <div class="match-score">
                                        <div class="info-grid">
                                            <div class="info-item">
                                                <i class="fas fa-globe"></i>
                                                <span><strong>Country:</strong> {detail['country']}</span>
                                            </div>
                                            <div class="info-item">
                                                <i class="fas fa-trophy"></i>
                                                <span><strong>World Rank:</strong> #{detail['ranking']}</span>
                                            </div>
                                            <div class="info-item">
                                                <i class="fas fa-dollar-sign"></i>
                                                <span><strong>Tuition:</strong> {detail['tuition']}</span>
                                            </div>
                                            <div class="info-item">
                                                <i class="fas fa-building"></i>
                                                <span><strong>Type:</strong> {detail['type']}</span>
                                            </div>
                                            <div class="info-item">
                                                <i class="fas fa-clock"></i>
                                                <span><strong>Duration:</strong> {detail['duration']}</span>
                                            </div>
                                            <div class="info-item">
                                                <i class="fas fa-language"></i>
                                                <span><strong>IELTS:</strong> {detail['ielts']} <strong>| TOEFL:</strong> {detail['toefl']}</span>
                                            </div>
                                        </div>
                                    </div>
                                    """ if detail else ''}
                                </div>
                                ''' for i, detail in enumerate(uni_details)]) + '''
                            </div>
                            
                            <div class="action-buttons">
                                <a href="/graduate" class="btn-custom btn-primary-custom">
                                    <i class="fas fa-search"></i>
                                    <span>Find More Universities</span>
                                </a>
                                <a href="/main" class="btn-custom btn-secondary-custom">
                                    <i class="fas fa-home"></i>
                                    <span>Back to Home</span>
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js"></script>
                    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js"></script>
                </body>
            </html>
                '''
    except Exception as e:
        print(f"Error in graduatealgo: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'''
            <html>
                <head>
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css">
                </head>
                <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 50px;">
                    <div class="container">
                        <div style="background: white; padding: 40px; border-radius: 20px; max-width: 600px; margin: 0 auto;">
                            <h1 style="color: #dc3545;">Error</h1>
                            <p>An error occurred while processing your request:</p>
                            <pre style="background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto;">{str(e)}</pre>
                            <p style="margin-top: 20px;">
                                <a href="/graduate" class="btn btn-primary">Try Again</a>
                                <a href="/main" class="btn btn-secondary">Go Home</a>
                            </p>
                        </div>
                    </div>
                </body>
            </html>
        '''



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
