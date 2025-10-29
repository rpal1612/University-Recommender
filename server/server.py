import random
from flask import Flask, render_template, request, redirect, jsonify, session
from flask_session import Session
from markupsafe import escape
import pandas as pd
import numpy as np
import csv
import math
from sklearn import neighbors, datasets
from numpy.random import permutation
from sklearn.metrics import precision_recall_fscore_support
import os
import sys
from datetime import datetime, timedelta

# Import configuration and custom modules
from config import DevelopmentConfig
from database import Database
from auth import auth_bp, init_auth, login_required, admin_required
from collaborative_filter import CollaborativeFilter

# Initialize Flask app
app = Flask(__name__, static_folder='../static', template_folder='../static')
app.config.from_object(DevelopmentConfig)

# Initialize Flask-Session
Session(app)

# Cache for collaborative groups (refresh every 30 minutes)
groups_cache = {
    'data': None,
    'timestamp': None
}

# Initialize MongoDB database
try:
    db = Database(app.config['MONGODB_URI'], app.config['MONGODB_DB_NAME'])
    print("✓ Database initialized successfully")
except Exception as e:
    print(f"✗ Database initialization failed: {e}")
    print("⚠ Application will run in limited mode without user features")
    db = None

# Initialize authentication
if db:
    init_auth(db)
    app.register_blueprint(auth_bp)
    print("✓ Authentication system initialized")

# Initialize collaborative filtering
collab_filter = CollaborativeFilter(db, weight=0.3) if db else None

# Load and prepare enhanced data once at startup for better performance
print("Loading and preparing real university data...")
import os
from typing import Dict, Any, List
import io

# Primary expected path (original project layout)
primary_csv = os.path.join(os.path.dirname(__file__), '..', 'WebScraped_data', 'csv', 'Real_University_Data.csv')
# Fallback path present in this repository (top-level `csv/` folder)
fallback_csv = os.path.join(os.path.dirname(__file__), '..', 'csv', 'Real_University_Data.csv')

if os.path.exists(primary_csv):
    csv_path = primary_csv
    print(f"Using CSV at {csv_path}")
elif os.path.exists(fallback_csv):
    csv_path = fallback_csv
    print(f"Primary CSV not found; using fallback CSV at {csv_path}")
else:
    # Provide a helpful error message listing both attempted paths
    raise FileNotFoundError(f"Real_University_Data.csv not found. Tried: {primary_csv} and {fallback_csv}")

def _load_clean_university_csv(path: str) -> pd.DataFrame:
    """Load CSV while removing git merge markers and duplicate header rows."""
    markers = ('<<<<<<<', '=======', '>>>>>>>')
    header_line = None
    cleaned_lines: List[str] = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.strip('\n')
            # Skip merge marker lines entirely
            if any(line.startswith(m) for m in markers):
                continue
            # Capture the first valid header (contains key columns)
            if header_line is None:
                if (
                    'greV' in line and 'greQ' in line and 'greA' in line and
                    'cgpa' in line and 'univName' in line and 'country' in line
                ):
                    header_line = line
                    cleaned_lines.append(line + '\n')
                # else keep scanning until we find the header
            else:
                # Skip repeated header occurrences inside the file
                if line == header_line:
                    continue
                cleaned_lines.append(line + '\n')
    if not cleaned_lines:
        raise ValueError(f"Failed to parse CSV at {path}: no valid data found")
    buf = io.StringIO(''.join(cleaned_lines))
    df = pd.read_csv(buf)
    # Drop unnamed index columns and duplicates
    df.drop(df.columns[df.columns.str.contains('unnamed', case=False)], axis=1, inplace=True, errors='ignore')
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

data = _load_clean_university_csv(csv_path)

print(f"Loaded {len(data)} universities with columns: {list(data.columns)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graduate')
@login_required
def graduate():
    return render_template('graduate.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect admins to admin dashboard
    if session.get('user_role') == 'admin':
        return redirect('/admin')
    return render_template('dashboard.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin.html')

@app.route('/api/check-auth')
def check_auth():
    """Check if user is authenticated"""
    return jsonify({
        'authenticated': 'user_id' in session,
        'role': session.get('user_role', 'user')
    })

@app.route('/api/user')
@login_required
def get_user_data():
    """Get current user data and statistics"""
    try:
        user_id = session.get('user_id')
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user statistics
        history = db.get_user_history(user_id)
        wishlist = db.get_wishlist(user_id)
        
        # Calculate unique universities
        unique_universities = set()
        for entry in history:
            if 'recommendations' in entry:
                for rec in entry['recommendations']:
                    unique_universities.add(rec.get('university_name'))
        
        stats = {
            'total_searches': len(history),
            'unique_universities': len(unique_universities),
            'wishlist_count': len(wishlist)
        }
        
        # Remove sensitive data
        user_data = {
            'name': user.get('name'),
            'email': user.get('email'),
            'role': user.get('role', 'user'),
            'memberSince': user.get('created_at')
        }
        
        return jsonify({
            'user': user_data,
            'stats': stats
        })
    except Exception as e:
        print(f"Error getting user data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/main")
def return_main():
    return render_template('index.html')

@app.route('/api/countries')
def get_countries():
    """Return unique countries from dataset"""
    try:
        countries = sorted(data['country'].unique().tolist())
        return jsonify(countries)
    except Exception as e:
        print(f"Error getting countries: {e}")
        # Fallback
        return jsonify(['USA', 'UK', 'Canada', 'Australia', 'Germany', 'Netherlands', 'Singapore', 'Switzerland'])

@app.route('/api/fields')
def get_fields():
    """Return unique fields of study from dataset"""
    try:
        fields = sorted(data['program_fields'].dropna().unique().tolist())
        return jsonify(fields)
    except Exception as e:
        print(f"Error getting fields: {e}")
        # Fallback
        return jsonify(['Computer Science,Engineering', 'Data Science,AI', 'Business,Management', 
                       'Engineering,Robotics', 'Mathematics,Statistics', 'Physics,Applied Sciences'])

@app.route('/api/history')
@login_required
def get_history():
    """Get user's search history"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        user_id = session.get('user_id')
        history = db.get_user_history(user_id, limit=20)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        }), 200
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500

@app.route('/api/history/<search_id>', methods=['DELETE'])
@login_required
def delete_history_item(search_id):
    """Delete a specific search from history"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        user_id = session.get('user_id')
        success = db.delete_search(user_id, search_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Search deleted'}), 200
        else:
            return jsonify({'error': 'Search not found'}), 404
    except Exception as e:
        print(f"Error deleting history: {e}")
        return jsonify({'error': 'Failed to delete search'}), 500

# ==================== WISHLIST API ROUTES ====================

@app.route('/api/wishlist', methods=['GET'])
@login_required
def get_wishlist():
    """Get user's wishlist"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        user_id = session.get('user_id')
        wishlist = db.get_wishlist(user_id)
        
        return jsonify({
            'success': True,
            'wishlist': wishlist,
            'count': len(wishlist)
        }), 200
    except Exception as e:
        print(f"Error getting wishlist: {e}")
        return jsonify({'error': 'Failed to fetch wishlist'}), 500

@app.route('/api/wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    """Add university to wishlist"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error': 'University name is required'}), 400
        
        success = db.add_to_wishlist(user_id, data)
        
        if success:
            return jsonify({'success': True, 'message': 'Added to wishlist'}), 200
        else:
            return jsonify({'error': 'Failed to add to wishlist'}), 500
    except Exception as e:
        print(f"Error adding to wishlist: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to add to wishlist: {str(e)}'}), 500

@app.route('/api/wishlist/<university_name>', methods=['DELETE'])
@login_required
def remove_from_wishlist(university_name):
    """Remove university from wishlist"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        user_id = session.get('user_id')
        success = db.remove_from_wishlist(user_id, university_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Removed from wishlist'}), 200
        else:
            return jsonify({'error': 'Not found in wishlist'}), 404
    except Exception as e:
        print(f"Error removing from wishlist: {e}")
        return jsonify({'error': 'Failed to remove from wishlist'}), 500

# ==================== ADMIN API ROUTES ====================

@app.route('/api/admin/stats')
@admin_required
def get_admin_stats():
    """Get system-wide statistics (admin only)"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        stats = db.get_system_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@app.route('/api/admin/users')
@admin_required
def get_admin_users():
    """Get all users with stats (admin only)"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        users = db.get_all_users_with_stats()
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        }), 200
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/api/admin/groups')
@admin_required
def get_admin_groups():
    """Get collaborative filtering groups (admin only) - with caching"""
    try:
        if not db:
            return jsonify({'error': 'Database not available'}), 503
        
        # Check cache (30 minute expiry)
        now = datetime.now()
        if groups_cache['data'] is not None and groups_cache['timestamp'] is not None:
            cache_age = (now - groups_cache['timestamp']).total_seconds()
            if cache_age < 1800:  # 30 minutes
                print(f"Returning cached groups (age: {int(cache_age)}s)")
                return jsonify({
                    'success': True,
                    'groups': groups_cache['data'],
                    'count': len(groups_cache['data']),
                    'cached': True
                }), 200
        
        # Calculate groups (this takes time)
        print("Calculating collaborative groups (cache expired or empty)...")
        groups = db.get_user_collaborative_groups()
        
        # Update cache
        groups_cache['data'] = groups
        groups_cache['timestamp'] = now
        
        return jsonify({
            'success': True,
            'groups': groups,
            'count': len(groups),
            'cached': False
        }), 200
    except Exception as e:
        print(f"Error getting groups: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch groups'}), 500


def calculate_comprehensive_score(user_data, uni_row):
    """
    OPTIMIZED scoring with feature engineering:
    - Academic Match (30%) - Uses engineered academic_strength
    - University Prestige (25%) - Ranking + research reputation
    - Field Alignment (20%) - Program match
    - Affordability (15%) - Cost vs budget
    - Language Fit (5%) - IELTS/TOEFL match
    - Preferences Alignment (5%) - Research/Internship/Visa
    """
    score = 0
    details = {}
    
    # Calculate user's academic strength using same formula as dataset
    user_greV_norm = (user_data['greV'] - 130) / 40
    user_greQ_norm = (user_data['greQ'] - 130) / 40
    user_greA_norm = user_data['greA'] / 6.0
    user_cgpa_norm = user_data['cgpa'] / 4.0
    
    user_academic_strength = (
        user_greV_norm * 0.25 + 
        user_greQ_norm * 0.35 +
        user_greA_norm * 0.15 + 
        user_cgpa_norm * 0.25
    )
    
    # 1. Academic Match (30% weight) - How well user matches university requirements
    # Calculate university's academic strength from existing data
    uni_greV_norm = (uni_row.get('greV', 150) - 130) / 40
    uni_greQ_norm = (uni_row.get('greQ', 150) - 130) / 40
    uni_greA_norm = uni_row.get('greA', 4.0) / 6.0
    uni_cgpa_norm = uni_row.get('cgpa', 3.0) / 4.0
    
    uni_academic_strength = (
        uni_greV_norm * 0.25 + 
        uni_greQ_norm * 0.35 +
        uni_greA_norm * 0.15 + 
        uni_cgpa_norm * 0.25
    )
    
    # Score based on how close user is to university requirements
    if user_academic_strength >= uni_academic_strength:
        # User exceeds requirements - full score
        academic_score = min(1.0, 0.95 + (user_academic_strength - uni_academic_strength) * 0.1)
    else:
        # Below requirements - penalty
        academic_score = max(0, 1.0 - (uni_academic_strength - user_academic_strength) * 1.5)
    
    # Ensure score doesn't exceed 1.0
    academic_score = min(1.0, academic_score)
    score += academic_score * 0.30
    details['academic_match'] = round(academic_score * 0.30, 3)
    
    # 2. University Prestige (25% weight) - Ranking + research reputation
    # Calculate ranking score from actual ranking data
    ranking = uni_row.get('ranking', 999)
    if ranking <= 10:
        prestige_score = 1.0
    elif ranking <= 50:
        prestige_score = 0.9
    elif ranking <= 100:
        prestige_score = 0.7
    elif ranking <= 200:
        prestige_score = 0.5
    elif ranking <= 500:
        prestige_score = 0.3
    else:
        prestige_score = 0.2
    
    # Small boost for research universities if user has publications (capped at 1.0)
    publications = user_data.get('publications', 0)
    if publications > 2 and uni_row.get('research_focused', False):
        prestige_score = min(1.0, prestige_score + 0.05)
    
    # Small boost for work experience with professional programs (capped at 1.0)
    work_exp = user_data.get('workExperience', 0)
    if work_exp > 3 and uni_row.get('internship_opportunities', False):
        prestige_score = min(1.0, prestige_score + 0.05)
    
    score += prestige_score * 0.25
    details['university_prestige'] = round(prestige_score * 0.25, 3)
    
    # 3. Field Alignment (20% weight) - Program match
    field_score = 0
    if user_data.get('major'):
        program_fields = str(uni_row.get('program_fields', '')).lower()
        major_lower = user_data['major'].lower()
        
        # Exact match
        if major_lower in program_fields:
            field_score = 1.0
        else:
            # Check keyword matches
            major_keywords = major_lower.split()
            matches = sum(1 for keyword in major_keywords if len(keyword) > 2 and keyword in program_fields)
            if matches > 0:
                field_score = min(1.0, 0.6 + (matches / len(major_keywords)) * 0.4)
            else:
                # Minimal credit for related fields
                field_score = 0.2
    else:
        field_score = 0.5
    
    score += field_score * 0.20
    details['field_alignment'] = round(field_score * 0.20, 3)
    
    # 4. Affordability (15% weight) - Cost vs budget
    affordability_score = 0
    uni_fees = uni_row.get('tuition_usd', 0)
    budget_max = user_data.get('budgetMax', 100000)
    budget_min = user_data.get('budgetMin', 0)
    
    if uni_fees <= 0:
        # No tuition data available
        affordability_score = 0.5
    elif uni_fees <= budget_max:
        if uni_fees <= budget_min:
            # Way below budget - possibly too cheap, slight penalty
            affordability_score = 0.8
        else:
            # Within budget - calculate based on how close to budget range
            budget_mid = (budget_min + budget_max) / 2
            if uni_fees <= budget_mid:
                # Lower half of budget - very affordable
                affordability_score = 1.0
            else:
                # Upper half of budget - less affordable but still good
                affordability_score = 0.8 - ((uni_fees - budget_mid) / (budget_max - budget_mid)) * 0.3
    else:
        # Over budget - penalty
        overage = (uni_fees - budget_max) / budget_max
        affordability_score = max(0, 0.5 - overage)
    
    score += affordability_score * 0.15
    details['affordability'] = round(affordability_score * 0.15, 3)
    
    # 5. Language Fit (5% weight) - Reduced importance
    language_score = 0
    if user_data.get('ielts') and pd.notna(uni_row.get('ielts_min')):
        if user_data['ielts'] >= uni_row['ielts_min']:
            language_score = 1.0
        else:
            # Partial credit if close (within 0.5 points)
            diff = uni_row['ielts_min'] - user_data['ielts']
            language_score = max(0, 1 - (diff / 1.5))
    elif user_data.get('toefl') and pd.notna(uni_row.get('toefl_min')):
        if user_data['toefl'] >= uni_row['toefl_min']:
            language_score = 1.0
        else:
            diff = uni_row['toefl_min'] - user_data['toefl']
            language_score = max(0, 1 - (diff / 25))
    else:
        language_score = 0.7  # Neutral if no data
    
    score += language_score * 0.05
    details['language_fit'] = round(language_score * 0.05, 3)
    
    # 6. Preferences Alignment (5% weight) - Research/Internship/Visa
    preference_score = 0
    pref_count = 0
    
    # Country match is in filtering, not scoring
    
    # Research focus
    if user_data.get('researchFocus'):
        if uni_row.get('research_focused', False):
            preference_score += 1.0
        pref_count += 1
    
    # Internship opportunities
    if user_data.get('internshipOpportunities'):
        if uni_row.get('internship_opportunities', False):
            preference_score += 1.0
        pref_count += 1
    
    # Work visa
    if user_data.get('workVisa'):
        if uni_row.get('post_study_work_visa', False):
            preference_score += 1.0
        pref_count += 1
    
    # Duration match
    if user_data.get('duration') and user_data['duration'] != 'Any':
        desired_duration = int(user_data['duration'])
        if uni_row.get('duration_years') == desired_duration:
            preference_score += 1.0
        pref_count += 1
    
    if pref_count > 0:
        preference_score = preference_score / pref_count
    else:
        preference_score = 0.5
    
    score += preference_score * 0.05
    details['preferences'] = round(preference_score * 0.05, 3)
    
    # CRITICAL: Cap total score at 1.0 (100%) to prevent >100% matches
    score = min(1.0, score)
    
    details['total'] = round(score, 3)
    
    # Add percentage for display (will always be 0-100%)
    details['percentage'] = round(score * 100, 1)
    
    return score, details


def get_best_universities(user_data, top_n=15):
    """
    Get top N best universities based on comprehensive scoring
    """
    print(f"\n=== Starting University Recommendation Analysis ===")
    print(f"User Profile:")
    print(f"  GRE: V:{user_data['greV']}, Q:{user_data['greQ']}, A:{user_data['greA']}")
    print(f"  GPA: {user_data['cgpa']}")
    print(f"  Field: {user_data.get('major', 'N/A')}")
    print(f"  Experience: {user_data.get('workExperience', 0)} years, Publications: {user_data.get('publications', 0)}")
    
    # Step 1: Filter by field of study
    filtered_data = data.copy()
    if user_data.get('major'):
        major_lower = user_data['major'].lower()
        filtered_data = filtered_data[
            filtered_data['program_fields'].str.contains(major_lower, case=False, na=False) |
            filtered_data['program_fields'].isna()
        ]
        print(f"\nAfter field filter ({user_data['major']}): {len(filtered_data)} universities")
    
    # Step 2: Filter by countries (support multiple countries)
    if user_data.get('preferred_countries') and len(user_data['preferred_countries']) > 0:
        # Filter to include any of the selected countries
        filtered_data = filtered_data[filtered_data['country'].isin(user_data['preferred_countries'])]
        print(f"After country filter ({user_data['preferred_countries']}): {len(filtered_data)} universities")
    else:
        print(f"No country filter applied: {len(filtered_data)} universities")
    
    # Step 3: Filter by budget
    if user_data.get('budgetMin') and user_data.get('budgetMax'):
        filtered_data = filtered_data[
            (filtered_data['tuition_usd'].isna()) |
            ((filtered_data['tuition_usd'] >= user_data['budgetMin']) & 
             (filtered_data['tuition_usd'] <= user_data['budgetMax']))
        ]
        print(f"After budget filter (${user_data['budgetMin']}-${user_data['budgetMax']}): {len(filtered_data)} universities")
    
    # Step 5: Filter by university type
    if user_data.get('universityType') and user_data['universityType'] != 'Any':
        filtered_data = filtered_data[
            (filtered_data['university_type'] == user_data['universityType']) |
            filtered_data['university_type'].isna()
        ]
        print(f"After type filter ({user_data['universityType']}): {len(filtered_data)} universities")
    
    # Step 6: Filter by duration
    if user_data.get('duration') and user_data['duration'] != 'Any':
        try:
            desired_duration = int(user_data['duration'])
            filtered_data = filtered_data[
                (filtered_data['duration_years'] == desired_duration) |
                filtered_data['duration_years'].isna()
            ]
            print(f"After duration filter ({desired_duration} year): {len(filtered_data)} universities")
        except (ValueError, TypeError):
            print(f"Invalid duration value: {user_data['duration']}, skipping duration filter")
    
    # Step 7: Calculate comprehensive scores for all filtered universities
    print(f"\n=== Calculating Comprehensive Scores ===")
    scores_list = []
    for idx, row in filtered_data.iterrows():
        score, details = calculate_comprehensive_score(user_data, row)
        scores_list.append({
            'idx': idx,
            'score': score,
            'details': details,
            'uni_name': row['univName'],
            'country': row.get('country', 'N/A'),
            'ranking': row.get('ranking', 'N/A')
        })
    
    # Sort by score
    scores_list.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nTop 5 Scores:")
    for i, item in enumerate(scores_list[:5], 1):
        print(f"  {i}. {item['uni_name']} ({item['country']}) - Score: {item['score']:.3f}")
        print(f"     Breakdown: {item['details']}")
    
    # Get top N unique universities with country diversity
    seen_universities = set()
    country_counts = {}
    top_universities = []
    
    # Initialize country counts for selected countries
    if user_data.get('preferred_countries'):
        for country in user_data['preferred_countries']:
            country_counts[country] = 0
    
    # First pass: Try to get at least 2-3 universities from each selected country
    max_per_country = max(2, top_n // len(user_data.get('preferred_countries', [1])))
    
    for item in scores_list:
        uni_name = item['uni_name']
        country = item['country']
        
        if uni_name not in seen_universities:
            # Check if we should add this university for diversity
            if not user_data.get('preferred_countries') or country_counts.get(country, 0) < max_per_country:
                seen_universities.add(uni_name)
                top_universities.append(item['idx'])
                country_counts[country] = country_counts.get(country, 0) + 1
                
                if len(top_universities) >= top_n:
                    break
    
    # Second pass: Fill remaining slots with best remaining universities
    if len(top_universities) < top_n:
        for item in scores_list:
            uni_name = item['uni_name']
            if uni_name not in seen_universities:
                seen_universities.add(uni_name)
                top_universities.append(item['idx'])
                if len(top_universities) >= top_n:
                    break
    
    print(f"\nSelected {len(top_universities)} unique universities")
    if user_data.get('preferred_countries'):
        print("Country distribution:")
        for country in user_data['preferred_countries']:
            count = country_counts.get(country, 0)
            print(f"  {country}: {count} universities")
    
    return top_universities, filtered_data, scores_list[:top_n]


@app.route('/graduatealgo', methods=['GET', 'POST'])
@login_required
def graduatealgo():
    try:
        import json as _json
        # Get request data
        src_args = request.form if request.method == 'POST' else request.args
        
        # Get basic academic scores
        greV = float(src_args.get("greV"))
        greQ = float(src_args.get("greQ"))
        greA = float(src_args.get("greA"))
        cgpa = float(src_args.get("cgpa"))
        
        # Get language proficiency
        englishTest = src_args.get("englishTest", "None")
        ielts = float(src_args.get("ielts", 0)) if src_args.get("ielts") else None
        toefl = float(src_args.get("toefl", 0)) if src_args.get("toefl") else None
        
        # Get academic background
        major = src_args.get("major", "")
        
        # Get professional experience
        workExperience = float(src_args.get("workExperience", 0))
        publications = int(src_args.get("publications", 0))
        
        # Get preferences
        budgetMin = float(src_args.get("budgetMin", 0))
        budgetMax = float(src_args.get("budgetMax", 100000))
        universityType = src_args.get("universityType", "Any")
        duration = src_args.get("duration", "Any")  # Keep as string to handle "Any"
        
        # Get boolean preferences
        researchFocus = src_args.get("researchFocus") == "true"
        internshipOpportunities = src_args.get("internshipOpportunities") == "true"
        workVisa = src_args.get("workVisa") == "true"
        
        # Simplified country selection - support multiple countries
        if request.method == 'POST':
            preferred_countries = request.form.getlist('preferred_countries')
        else:
            preferred_countries = request.args.getlist('preferred_countries')
        
        # Keep all selected countries for multi-country recommendations
        if preferred_countries and len(preferred_countries) > 0:
            # Remove any empty or invalid selections
            preferred_countries = [c.strip() for c in preferred_countries if c and c.strip()]
        else:
            preferred_countries = []
        
        print(f"\n{'='*60}")
        print(f"Processing Comprehensive Recommendation Request")
        print(f"{'='*60}")
        print(f"Academic: GRE V:{greV}, Q:{greQ}, A:{greA}, GPA:{cgpa}")
        print(f"Language: {englishTest} - IELTS:{ielts}, TOEFL:{toefl}")
        print(f"Background: Major:{major}, Experience:{workExperience}y, Publications:{publications}")
        print(f"Selected Countries: {preferred_countries} ({len(preferred_countries)} countries)")
        print(f"Budget: ${budgetMin}-${budgetMax}")
        print(f"Filters: Type:{universityType}, Duration:{duration}")
        print(f"Boolean Prefs: Research:{researchFocus}, Internship:{internshipOpportunities}, Visa:{workVisa}")
        print(f"{'='*60}\\n")
        
        # Build user data dictionary
        user_data = {
            'greV': greV,
            'greQ': greQ,
            'greA': greA,
            'cgpa': cgpa,
            'major': major,
            'workExperience': workExperience,
            'publications': publications,
            'preferred_countries': preferred_countries,  # List of selected countries
            'budgetMin': budgetMin,
            'budgetMax': budgetMax,
            'universityType': universityType,
            'duration': duration,
            'researchFocus': researchFocus,
            'internshipOpportunities': internshipOpportunities,
            'workVisa': workVisa
        }
        
        if ielts:
            user_data['ielts'] = ielts
        if toefl:
            user_data['toefl'] = toefl
        
        # Get best universities using content-based filtering
        top_indices, filtered_df, score_details = get_best_universities(user_data, top_n=15)
        
        # Build university details
        uni_details = []
        for i, score_item in enumerate(score_details):
            idx = score_item['idx']
            if idx not in filtered_df.index:
                continue
            
            uni_row = filtered_df.loc[idx]
            
            # Convert numpy types to Python native types for JSON serialization
            ranking_val = uni_row.get('ranking')
            ranking = int(ranking_val) if pd.notna(ranking_val) else 999
            
            tuition_val = uni_row.get('tuition_usd')
            tuition_int = int(tuition_val) if pd.notna(tuition_val) else 0
            
            duration_val = uni_row.get('duration_years')
            duration_int = int(duration_val) if pd.notna(duration_val) else 1
            
            ielts_val = uni_row.get('ielts_min')
            ielts_float = float(ielts_val) if pd.notna(ielts_val) else None
            
            toefl_val = uni_row.get('toefl_min')
            toefl_int = int(toefl_val) if pd.notna(toefl_val) else None
            
            uni_details.append({
                'name': str(uni_row['univName']),
                'country': str(uni_row.get('country', 'N/A')),
                'ranking': ranking,
                'tuition': f"${tuition_int:,}" if tuition_int > 0 else 'Contact University',
                'tuition_value': tuition_int,
                'type': str(uni_row.get('university_type', 'N/A')),
                'duration': f"{duration_int} year{'s' if duration_int > 1 else ''}",
                'ielts': ielts_float if ielts_float else 'N/A',
                'toefl': toefl_int if toefl_int else 'N/A',
                'score': float(score_item['score']),
                'score_breakdown': score_item['details'],
                'research_focused': bool(uni_row.get('research_focused', False)),
                'internship_opportunities': bool(uni_row.get('internship_opportunities', False)),
                'post_study_work_visa': bool(uni_row.get('post_study_work_visa', False)),
            })
        
        # Apply collaborative filtering if user is logged in and database is available
        if db and 'user_id' in session and collab_filter:
            try:
                print("\n=== Applying Hybrid Filtering (Content + Collaborative) ===")
                uni_details = collab_filter.get_hybrid_recommendations(
                    session['user_id'], 
                    uni_details, 
                    limit=15
                )
                print(f"✓ Hybrid recommendations generated")
            except Exception as e:
                print(f"⚠ Collaborative filtering failed, using content-based only: {e}")
        
        print(f"\n=== Final Recommendations ===")
        for i, detail in enumerate(uni_details[:10], 1):
            score_info = f"Hybrid: {detail.get('hybrid_score', detail['score']):.2f}" if 'hybrid_score' in detail else f"Score: {detail['score']:.3f}"
            collab_badge = " [✓ Collab]" if detail.get('has_collaborative') else ""
            print(f"{i}. {detail['name']} ({detail['country']}) - {score_info}, Rank: {detail['ranking']}{collab_badge}")
        
        # Save search history if user is logged in
        if db and 'user_id' in session:
            try:
                search_data = {
                    'greV': greV,
                    'greQ': greQ,
                    'greA': greA,
                    'cgpa': cgpa,
                    'ielts': ielts,
                    'toefl': toefl,
                    'major': major,
                    'workExperience': workExperience,
                    'publications': publications,
                    'country': preferred_countries,
                    'budgetMin': budgetMin,
                    'budgetMax': budgetMax,
                    'universityType': universityType,
                    'duration': duration,
                    'researchFocus': researchFocus,
                    'internshipOpportunities': internshipOpportunities,
                    'workVisa': workVisa
                }
                
                # Simplify recommendations for storage
                recommendations = [{
                    'name': uni['name'],
                    'country': uni['country'],
                    'score': uni.get('hybrid_score', uni['score']),
                    'ranking': uni['ranking']
                } for uni in uni_details]
                
                search_id = db.save_search(session['user_id'], search_data, recommendations)
                print(f"✓ Search history saved (ID: {search_id})")
            except Exception as e:
                print(f"⚠ Failed to save search history: {e}")
        
        # Generate results HTML with filtering capabilities
        return generate_results_html(uni_details, user_data)
        
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


def generate_results_html(uni_details, user_data):
    """Generate interactive results HTML with external CSS/JS files"""
    
    import json
    uni_json = json.dumps(uni_details)
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your University Matches</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="/static/css/results.css">
</head>
<body>
    <!-- Top Navigation -->
    <div class="top-nav">
        <div class="logo">
            <i class="fas fa-graduation-cap"></i>
            University Recommender
        </div>
        <div>
            <a href="/graduate" class="nav-btn"><i class="fas fa-search"></i> New Search</a>
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Fixed Sidebar with Filters -->
        <div class="sidebar results-sidebar">
            <h3><i class="fas fa-user-circle"></i> Your Profile</h3>
            
            <!-- Stats Summary -->
            <div class="stats-box">
                <h4>📊 Quick Stats</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value">{user_data['greV'] + user_data['greQ']}</span>
                        <span class="stat-label">Total GRE</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{user_data['cgpa']}</span>
                        <span class="stat-label">GPA</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{user_data.get('workExperience', 0)}</span>
                        <span class="stat-label">Years Exp</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(uni_details)}</span>
                        <span class="stat-label">Matches</span>
                    </div>
                </div>
            </div>
            
            <h3><i class="fas fa-filter"></i> Filters</h3>
            
            <!-- Sort By -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-sort"></i> Sort By
                </div>
                <select id="sortBy" onchange="applyFilters()">
                    <option value="score">Match Score (High to Low)</option>
                    <option value="fees-low">Tuition (Low to High)</option>
                    <option value="fees-high">Tuition (High to Low)</option>
                    <option value="country">Country (A-Z)</option>
                </select>
            </div>
            
            <!-- Filter by Country -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-globe"></i> Country
                </div>
                <select id="filterCountry" onchange="applyFilters()">
                    <option value="">All Countries</option>
                </select>
            </div>
            
            <!-- Filter by Type -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-university"></i> University Type
                </div>
                <select id="filterType" onchange="applyFilters()">
                    <option value="">All Types</option>
                    <option value="Public">Public</option>
                    <option value="Private">Private</option>
                </select>
            </div>
            
            <!-- Filter by Budget -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-dollar-sign"></i> Max Budget
                </div>
                <select id="filterBudget" onchange="applyFilters()">
                    <option value="999999">Any Budget</option>
                    <option value="20000">Under $20,000</option>
                    <option value="30000">Under $30,000</option>
                    <option value="40000">Under $40,000</option>
                    <option value="50000">Under $50,000</option>
                </select>
            </div>
            
            <button class="reset-btn" onclick="resetFilters()">
                <i class="fas fa-redo"></i> Reset All Filters
            </button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            <div class="results-header">
                <h1><i class="fas fa-trophy"></i> Your Top University Matches</h1>
                <p class="results-count">Showing <strong id="resultsCount">{len(uni_details)}</strong> universities</p>
            </div>
            
            <div class="universities-grid" id="universitiesList"></div>
        </div>
    </div>
    
    <script>
        // Inject universities data
        const universitiesData = {uni_json};
    </script>
    <script src="/static/js/results.js"></script>
</body>
</html>
    '''
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your University Matches</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }}
        
        /* Top Navigation */
        .top-nav {{
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            padding: 1rem 2rem;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .nav-btn {{
            padding: 8px 20px;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            color: #667eea;
            background: transparent;
            text-decoration: none;
            transition: all 0.3s;
            margin-left: 10px;
        }}
        
        .nav-btn:hover {{
            background: #f0f0f0;
        }}
        
        /* Main Layout */
        .main-container {{
            display: flex;
            margin-top: 70px;
            min-height: calc(100vh - 70px);
        }}
        
        /* Fixed Sidebar */
        .sidebar {{
            width: 320px;
            background: #ffffff;
            box-shadow: 2px 0 15px rgba(0,0,0,0.08);
            overflow-y: auto;
            padding: 30px 25px;
            position: fixed;
            left: 0;
            top: 70px;
            bottom: 0;
        }}
        
        .sidebar::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .sidebar::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 3px;
        }}
        
        .sidebar h3 {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        /* Stats Summary in Sidebar */
        .stats-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 25px;
            color: white;
        }}
        
        .stats-box h4 {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 15px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: 800;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        /* Filter Controls */
        .filter-group {{
            margin-bottom: 20px;
        }}
        
        .filter-label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .filter-label i {{
            color: #667eea;
        }}
        
        select {{
            width: 100%;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 0.9rem;
            background: #fafafa;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        select:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: #ffffff;
            outline: none;
        }}
        
        .reset-btn {{
            width: 100%;
            padding: 12px;
            background: #f0f0f0;
            color: #667eea;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s;
        }}
        
        .reset-btn:hover {{
            background: #667eea;
            color: white;
        }}
        
        /* Content Area */
        .content-area {{
            margin-left: 320px;
            padding: 30px;
            flex: 1;
            background: #f5f7fa;
        }}
        
        .results-header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
            text-align: center;
        }}
        
        .results-header h1 {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        
        .results-count {{
            font-size: 1.1rem;
            color: #666;
        }}
        
        /* University Cards */
        .university-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
            transition: all 0.3s;
            position: relative;
            border-left: 4px solid #667eea;
        }}
        
        .university-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }}
        
        .university-name {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .university-name h3 {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
        }}
        
        .google-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 35px;
            height: 35px;
            background: linear-gradient(135deg, #4285f4 0%, #ea4335 100%);
            border-radius: 50%;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
        }}
        
        .google-link:hover {{
            transform: scale(1.1);
        }}
        
        .match-badge {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1rem;
            white-space: nowrap;
        }}
        
        .score-breakdown {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .breakdown-title {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }}
        
        .breakdown-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 8px;
            font-size: 0.85rem;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
        }}
        
        .breakdown-item strong {{
            color: #333;
        }}
        
        .breakdown-item span {{
            color: #667eea;
            font-weight: 600;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }}
        
        .info-item {{
            background: #f5f7fa;
            padding: 10px 12px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }}
        
        .info-item i {{
            color: #667eea;
        }}
        
        .info-item strong {{
            color: #333;
        }}
        
        .feature-tags {{
            display: flex;
            gap: 8px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .feature-tag {{
            background: #e8ebf7;
            color: #667eea;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .no-results {{
            background: white;
            border-radius: 15px;
            padding: 60px;
            text-align: center;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }}
        
        .no-results i {{
            font-size: 4rem;
            color: #667eea;
            margin-bottom: 20px;
        }}
        
        .no-results h3 {{
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .no-results p {{
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .sidebar {{
                width: 100%;
                position: relative;
                top: 0;
            }}
            .content-area {{
                margin-left: 0;
            }}
            .main-container {{
                flex-direction: column;
            }}
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <!-- Top Navigation -->
    <div class="top-nav">
        <div class="logo">
            <i class="fas fa-graduation-cap"></i>
            University Recommender
        </div>
        <div>
            <a href="/graduate" class="nav-btn"><i class="fas fa-search"></i> New Search</a>
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Fixed Sidebar with Filters -->
        <div class="sidebar">
            <h3><i class="fas fa-user-circle"></i> Your Profile</h3>
            
            <!-- Stats Summary -->
            <div class="stats-box">
                <h4>📊 Quick Stats</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value">{user_data['greV'] + user_data['greQ']}</span>
                        <span class="stat-label">Total GRE</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{user_data['cgpa']}</span>
                        <span class="stat-label">GPA</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{user_data.get('workExperience', 0)}</span>
                        <span class="stat-label">Years Exp</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(uni_details)}</span>
                        <span class="stat-label">Matches</span>
                    </div>
                </div>
            </div>
            
            <h3><i class="fas fa-filter"></i> Filters</h3>
            
            <!-- Sort By -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-sort"></i> Sort By
                </div>
                <select id="sortBy" onchange="applyFilters()">
                    <option value="score">Match Score (High to Low)</option>
                    <option value="fees-low">Tuition (Low to High)</option>
                    <option value="fees-high">Tuition (High to Low)</option>
                    <option value="country">Country (A-Z)</option>
                </select>
            </div>
            
            <!-- Filter by Country -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-globe"></i> Country
                </div>
                <select id="filterCountry" onchange="applyFilters()">
                    <option value="">All Countries</option>
                </select>
            </div>
            
            <!-- Filter by Type -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-university"></i> University Type
                </div>
                <select id="filterType" onchange="applyFilters()">
                    <option value="">All Types</option>
                    <option value="Public">Public</option>
                    <option value="Private">Private</option>
                </select>
            </div>
            
            <!-- Filter by Budget -->
            <div class="filter-group">
                <div class="filter-label">
                    <i class="fas fa-dollar-sign"></i> Max Budget
                </div>
                <select id="filterBudget" onchange="applyFilters()">
                    <option value="999999">Any Budget</option>
                    <option value="20000">Under $20,000</option>
                    <option value="30000">Under $30,000</option>
                    <option value="40000">Under $40,000</option>
                    <option value="50000">Under $50,000</option>
                </select>
            </div>
            
            <button class="reset-btn" onclick="resetFilters()">
                <i class="fas fa-redo"></i> Reset All Filters
            </button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            <div class="results-header">
                <h1><i class="fas fa-trophy"></i> Your Top University Matches</h1>
                <p class="results-count">Showing <strong id="resultsCount">{len(uni_details)}</strong> universities</p>
            </div>
            
            <div id="universitiesList"></div>
        </div>
    </div>
    
    <script>
        let allUniversities = {uni_json};
        let filteredUniversities = [...allUniversities];
        
        document.addEventListener('DOMContentLoaded', function() {{
            populateCountryFilter();
            applyFilters();
        }});
        
        function populateCountryFilter() {{
            const countries = [...new Set(allUniversities.map(u => u.country))].sort();
            const select = document.getElementById('filterCountry');
            countries.forEach(country => {{
                const option = document.createElement('option');
                option.value = country;
                option.textContent = country;
                select.appendChild(option);
            }});
        }}
        
        function applyFilters() {{
            const sortBy = document.getElementById('sortBy').value;
            const filterCountry = document.getElementById('filterCountry').value;
            const filterType = document.getElementById('filterType').value;
            const filterBudget = parseInt(document.getElementById('filterBudget').value);
            
            // Filter
            filteredUniversities = allUniversities.filter(uni => {{
                if (filterCountry && uni.country !== filterCountry) return false;
                if (filterType && uni.type !== filterType) return false;
                if (filterBudget < 999999 && uni.tuition_value > filterBudget) return false;
                return true;
            }});
            
            // Sort
            filteredUniversities.sort((a, b) => {{
                switch(sortBy) {{
                    case 'score':
                        return (b.score || 0) - (a.score || 0);
                    case 'fees-low':
                        return (a.tuition_value || 999999) - (b.tuition_value || 999999);
                    case 'fees-high':
                        return (b.tuition_value || 0) - (a.tuition_value || 0);
                    case 'country':
                        return a.country.localeCompare(b.country);
                    default:
                        return (b.score || 0) - (a.score || 0);
                }}
            }});
            
            displayUniversities();
        }}
        
        function resetFilters() {{
            document.getElementById('sortBy').value = 'score';
            document.getElementById('filterCountry').value = '';
            document.getElementById('filterType').value = '';
            document.getElementById('filterBudget').value = '999999';
            applyFilters();
        }}
        
        function displayUniversities() {{
            const container = document.getElementById('universitiesList');
            document.getElementById('resultsCount').textContent = filteredUniversities.length;
            
            if (filteredUniversities.length === 0) {{
                container.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <h3>No Matches Found</h3>
                        <p>Try adjusting your filters to see more universities</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = filteredUniversities.map((uni, index) => `
                <div class="university-card">
                    <div class="card-header">
                        <div class="university-name">
                            <i class="fas fa-university" style="color: #667eea; font-size: 1.5rem;"></i>
                            <h3>${{uni.name}}</h3>
                            <a href="https://www.google.com/search?q=${{encodeURIComponent(uni.name)}}" 
                               target="_blank" 
                               class="google-link" 
                               title="Search on Google">
                                <i class="fab fa-google"></i>
                            </a>
                        </div>
                        <div class="match-badge">
                            ${{(uni.score * 100).toFixed(1)}}% Match
                        </div>
                    </div>
                    
                    <div class="score-breakdown">
                        <div class="breakdown-title">
                            <i class="fas fa-chart-bar"></i> Score Breakdown
                        </div>
                        <div class="breakdown-grid">
                            <div class="breakdown-item">
                                <strong>Academic:</strong>
                                <span>${{((uni.score_breakdown?.academic_match || 0) * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="breakdown-item">
                                <strong>Prestige:</strong>
                                <span>${{((uni.score_breakdown?.university_prestige || 0) * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="breakdown-item">
                                <strong>Field:</strong>
                                <span>${{((uni.score_breakdown?.field_alignment || 0) * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="breakdown-item">
                                <strong>Affordability:</strong>
                                <span>${{((uni.score_breakdown?.affordability || 0) * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="breakdown-item">
                                <strong>Language:</strong>
                                <span>${{((uni.score_breakdown?.language_fit || 0) * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="breakdown-item">
                                <strong>Preferences:</strong>
                                <span>${{((uni.score_breakdown?.preferences || 0) * 100).toFixed(1)}}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <i class="fas fa-globe"></i>
                            <span><strong>Country:</strong> ${{uni.country}}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-trophy"></i>
                            <span><strong>Rank:</strong> #${{uni.ranking === 999 ? 'N/A' : uni.ranking}}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-dollar-sign"></i>
                            <span><strong>Tuition:</strong> ${{uni.tuition}}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-building"></i>
                            <span><strong>Type:</strong> ${{uni.type}}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-clock"></i>
                            <span><strong>Duration:</strong> ${{uni.duration}}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-language"></i>
                            <span><strong>IELTS:</strong> ${{uni.ielts}} | <strong>TOEFL:</strong> ${{uni.toefl}}</span>
                        </div>
                    </div>
                    
                    <div class="feature-tags">
                        ${{uni.research_focused ? '<div class="feature-tag"><i class="fas fa-microscope"></i> Research-Focused</div>' : ''}}
                        ${{uni.internship_opportunities ? '<div class="feature-tag"><i class="fas fa-briefcase"></i> Internships</div>' : ''}}
                        ${{uni.post_study_work_visa ? '<div class="feature-tag"><i class="fas fa-passport"></i> Work Visa</div>' : ''}}
                    </div>
                </div>
            `).join('');
        }}
    </script>
</body>
</html>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
