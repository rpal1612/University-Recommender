"""
Populate database with 120 fresh users based on preference patterns
Groups will form automatically based on: Country, Course, and Score preferences
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from config import Config
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Load university data
print("✓ Connected to MongoDB: university_recommender")
print("Loading university data...")
data = pd.read_csv('../csv/Real_University_Data.csv')

# Define preference profiles (120 users total)
PREFERENCE_PROFILES = {
    'us_cs_high': {  # USA, Computer Science, High Scores (8.5+ CGPA)
        'count': 15,
        'countries': ['USA'],
        'majors': ['Computer Science', 'Data Science', 'Artificial Intelligence'],
        'cgpa_range': (8.5, 10.0),
        'gre_v_range': (155, 170),
        'gre_q_range': (165, 170),
        'budget_range': (40000, 80000),
        'target_unis': ['Stanford', 'MIT', 'Carnegie Mellon', 'Berkeley', 'Cornell']
    },
    'uk_cs_high': {  # UK, Computer Science, High Scores
        'count': 12,
        'countries': ['UK'],
        'majors': ['Computer Science', 'Software Engineering', 'Data Science'],
        'cgpa_range': (8.5, 10.0),
        'gre_v_range': (155, 170),
        'gre_q_range': (160, 170),
        'budget_range': (30000, 60000),
        'target_unis': ['Oxford', 'Cambridge', 'Imperial', 'UCL', 'Edinburgh']
    },
    'canada_cs_medium': {  # Canada, Computer Science, Medium Scores
        'count': 12,
        'countries': ['Canada'],
        'majors': ['Computer Science', 'Information Technology'],
        'cgpa_range': (7.0, 8.5),
        'gre_v_range': (145, 155),
        'gre_q_range': (155, 165),
        'budget_range': (20000, 40000),
        'target_unis': ['Toronto', 'UBC', 'Waterloo', 'McGill', 'Alberta']
    },
    'us_business_high': {  # USA, Business/MBA, High Scores
        'count': 10,
        'countries': ['USA'],
        'majors': ['Business Analytics', 'MBA', 'Finance'],
        'cgpa_range': (8.0, 10.0),
        'gre_v_range': (155, 170),
        'gre_q_range': (160, 170),
        'budget_range': (50000, 100000),
        'target_unis': ['Harvard', 'Stanford', 'Wharton', 'MIT Sloan', 'Chicago Booth']
    },
    'germany_engineering_medium': {  # Germany, Engineering, Medium Scores
        'count': 10,
        'countries': ['Germany'],
        'majors': ['Mechanical Engineering', 'Electrical Engineering', 'Civil Engineering'],
        'cgpa_range': (7.5, 8.5),
        'gre_v_range': (145, 155),
        'gre_q_range': (155, 165),
        'budget_range': (10000, 25000),
        'target_unis': ['TUM', 'RWTH Aachen', 'KIT', 'TU Berlin', 'Stuttgart']
    },
    'australia_cs_medium': {  # Australia, Computer Science, Medium Scores
        'count': 10,
        'countries': ['Australia'],
        'majors': ['Computer Science', 'Information Systems'],
        'cgpa_range': (7.0, 8.5),
        'gre_v_range': (145, 155),
        'gre_q_range': (150, 160),
        'budget_range': (25000, 50000),
        'target_unis': ['Melbourne', 'Sydney', 'ANU', 'UNSW', 'Queensland']
    },
    'us_data_science_high': {  # USA, Data Science, High Scores
        'count': 12,
        'countries': ['USA'],
        'majors': ['Data Science', 'Machine Learning', 'Statistics'],
        'cgpa_range': (8.5, 10.0),
        'gre_v_range': (150, 165),
        'gre_q_range': (165, 170),
        'budget_range': (35000, 75000),
        'target_unis': ['Stanford', 'CMU', 'Berkeley', 'MIT', 'Columbia']
    },
    'uk_business_medium': {  # UK, Business, Medium Scores
        'count': 8,
        'countries': ['UK'],
        'majors': ['Business Analytics', 'Marketing', 'Finance'],
        'cgpa_range': (7.0, 8.5),
        'gre_v_range': (145, 155),
        'gre_q_range': (150, 160),
        'budget_range': (25000, 50000),
        'target_unis': ['LSE', 'Warwick', 'Manchester', 'Birmingham', 'Bristol']
    },
    'canada_engineering_medium': {  # Canada, Engineering, Medium Scores
        'count': 8,
        'countries': ['Canada'],
        'majors': ['Electrical Engineering', 'Mechanical Engineering'],
        'cgpa_range': (7.0, 8.0),
        'gre_v_range': (140, 150),
        'gre_q_range': (150, 160),
        'budget_range': (18000, 35000),
        'target_unis': ['Toronto', 'Waterloo', 'UBC', 'McMaster', 'Alberta']
    },
    'singapore_cs_high': {  # Singapore, Computer Science, High Scores
        'count': 8,
        'countries': ['Singapore'],
        'majors': ['Computer Science', 'AI', 'Cybersecurity'],
        'cgpa_range': (8.5, 10.0),
        'gre_v_range': (150, 165),
        'gre_q_range': (165, 170),
        'budget_range': (30000, 55000),
        'target_unis': ['NUS', 'NTU']
    },
    'us_research_phd': {  # USA, Research/PhD, High Scores
        'count': 8,
        'countries': ['USA'],
        'majors': ['Computer Science', 'Physics', 'Biology', 'Chemistry'],
        'cgpa_range': (8.5, 10.0),
        'gre_v_range': (155, 170),
        'gre_q_range': (165, 170),
        'budget_range': (0, 30000),  # PhD usually funded
        'target_unis': ['MIT', 'Stanford', 'Harvard', 'Princeton', 'Yale']
    },
    'netherlands_diverse_medium': {  # Netherlands, Diverse fields, Medium Scores
        'count': 7,
        'countries': ['Netherlands'],
        'majors': ['Computer Science', 'Business', 'Engineering', 'Data Science'],
        'cgpa_range': (7.5, 8.5),
        'gre_v_range': (145, 155),
        'gre_q_range': (155, 165),
        'budget_range': (15000, 30000),
        'target_unis': ['TU Delft', 'Amsterdam', 'Utrecht', 'Eindhoven', 'Leiden']
    }
}

def generate_user(profile_name, profile, user_num):
    """Generate a single user with search history"""
    
    # Generate user data
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}{user_num}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'university.edu'])}"
    
    # Random scores within profile range
    cgpa = round(random.uniform(profile['cgpa_range'][0], profile['cgpa_range'][1]), 2)
    gre_v = random.randint(profile['gre_v_range'][0], profile['gre_v_range'][1])
    gre_q = random.randint(profile['gre_q_range'][0], profile['gre_q_range'][1])
    gre_a = round(random.uniform(3.5, 5.0), 1)
    ielts = round(random.uniform(7.0, 9.0), 1)
    toefl = random.randint(95, 120)
    
    user = {
        'name': f"{first_name} {last_name}",
        'email': email,
        'password': 'Password123',
        'cgpa': cgpa,
        'greV': gre_v,
        'greQ': gre_q,
        'greA': gre_a,
        'ielts': ielts,
        'toefl': toefl,
        'work_experience': random.randint(0, 5),
        'publications': random.randint(0, 3),
        'profile_type': profile_name
    }
    
    return user

def generate_searches(user, profile, db):
    """Generate 2-4 search histories for a user"""
    num_searches = random.randint(2, 4)
    
    for _ in range(num_searches):
        # Randomly select from profile preferences
        country = random.choice(profile['countries'])
        major = random.choice(profile['majors'])
        budget_min, budget_max = profile['budget_range']
        
        search_data = {
            'greV': user['greV'],
            'greQ': user['greQ'],
            'greA': user['greA'],
            'cgpa': user['cgpa'],
            'ielts': user['ielts'],
            'toefl': user['toefl'],
            'major': major,
            'workExperience': user['work_experience'],
            'publications': user['publications'],
            'country': [country],  # Keep as list for consistency
            'budgetMin': budget_min + random.randint(-5000, 5000),
            'budgetMax': budget_max + random.randint(-10000, 10000),
            'universityType': random.choice(['Public', 'Private', 'Any']),
            'duration': random.choice(['1 year', '2 years', 'Any']),
            'researchFocus': random.choice([True, False]),
            'internshipOpportunities': random.choice([True, False]),
            'workVisa': random.choice([True, False])
        }
        
        # Generate recommendations based on target universities
        recommendations = []
        target_unis = profile['target_unis']
        
        # Filter universities by country and add some from target list
        country_unis = data[data['country'].str.contains(country, case=False, na=False)]
        
        # Try to include target universities
        for uni_name in target_unis:
            matching = data[data['univName'].str.contains(uni_name, case=False, na=False)]
            if len(matching) > 0:
                uni = matching.iloc[0]
                recommendations.append({
                    'university_name': uni['univName'],
                    'country': uni['country'],
                    'course': major,
                    'match_score': round(random.uniform(0.7, 0.95), 2),
                    'tuition_fee': random.randint(budget_min, budget_max)
                })
        
        # Add random universities from the country
        if len(country_unis) > 0:
            num_random = min(random.randint(5, 10), len(country_unis))
            random_unis = country_unis.sample(n=num_random)
            
            for _, uni in random_unis.iterrows():
                if len(recommendations) < 15:
                    recommendations.append({
                        'university_name': uni['univName'],
                        'country': uni['country'],
                        'course': major,
                        'match_score': round(random.uniform(0.5, 0.85), 2),
                        'tuition_fee': random.randint(budget_min, budget_max)
                    })
        
        # Save search
        if len(recommendations) > 0:
            db.save_search(user['_id'], search_data, recommendations)

def main():
    """Main function to populate database"""
    print("=" * 60)
    print("POPULATING DATABASE WITH 120 FRESH USERS")
    print("Preference-based grouping: Country + Course + Score")
    print("=" * 60)
    
    # Connect to database
    db = Database(Config.MONGODB_URI, Config.MONGODB_DB_NAME)
    
    total_users = 0
    total_searches = 0
    total_recommendations = 0
    
    # Generate users for each profile
    for profile_name, profile in PREFERENCE_PROFILES.items():
        print(f"\n{'='*60}")
        print(f"Generating {profile['count']} users for: {profile_name.upper()}")
        print(f"  Countries: {', '.join(profile['countries'])}")
        print(f"  Majors: {', '.join(profile['majors'])}")
        print(f"  CGPA Range: {profile['cgpa_range'][0]} - {profile['cgpa_range'][1]}")
        print(f"{'='*60}")
        
        for i in range(profile['count']):
            # Generate user
            user = generate_user(profile_name, profile, total_users + 1)
            
            # Save user to database
            user_id = db.create_user(
                email=user['email'],
                password=user['password'],
                full_name=user['name']
            )
            
            if user_id:
                user['_id'] = user_id
                total_users += 1
                print(f"Created user {total_users}: {user['email']} ({profile_name})")
                
                # Generate searches for this user
                searches_before = db.search_history.count_documents({'user_id': str(user_id)})
                generate_searches(user, profile, db)
                searches_after = db.search_history.count_documents({'user_id': str(user_id)})
                
                user_searches = searches_after - searches_before
                total_searches += user_searches
                
                # Count recommendations
                user_recs = db.recommendations.count_documents({'user_id': str(user_id)})
                total_recommendations += user_recs
                
                if user_searches > 0:
                    print(f"  → Generated {user_searches} searches with {user_recs} recommendations")
    
    print("\n" + "=" * 60)
    print("✅ POPULATION COMPLETE!")
    print("=" * 60)
    print(f"Total users created: {total_users}")
    print(f"Total searches: {total_searches}")
    print(f"Total recommendations: {total_recommendations}")
    
    print("\n📊 User Distribution by Profile:")
    for profile_name, profile in PREFERENCE_PROFILES.items():
        print(f"  - {profile_name}: {profile['count']} users")
    
    print("\n🔐 All users have password: 'Password123'")
    
    print("\n✅ Groups will form automatically based on:")
    print("   1. Country Preference (USA, UK, Canada, etc.)")
    print("   2. Course Preference (CS, Business, Engineering, etc.)")
    print("   3. Score Range (High: 8.5+, Medium: 7-8.5, Low: <7)")
    
    print("\n🚀 Start your server and check the admin dashboard!")

if __name__ == "__main__":
    main()
