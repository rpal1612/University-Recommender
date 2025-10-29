"""
Populate MongoDB with 1000 realistic users and search history
to enable collaborative filtering without cold start issues
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from database import Database
import bcrypt
from bson import ObjectId

# Initialize database
MONGODB_URI = 'mongodb+srv://admin:admin@cluster0.lgez1ci.mongodb.net/?appName=Cluster0'
MONGODB_DB_NAME = 'university_recommender'
db = Database(MONGODB_URI, MONGODB_DB_NAME)

# Load university data
print("Loading university data...")
data = pd.read_csv('../csv/Real_University_Data.csv')

# Define user profiles and patterns
USER_PROFILES = {
    'elite_cs': {
        'count': 75,  # Reduced from 150
        'gre_v_range': (160, 170),
        'gre_q_range': (165, 170),
        'gre_a_range': (4.5, 6.0),
        'gpa_range': (3.7, 4.0),
        'majors': ['Computer Science', 'Artificial Intelligence', 'Data Science', 'Software Engineering'],
        'countries': ['USA', 'UK', 'Canada', 'Switzerland'],
        'budget_range': (40000, 80000),
        'work_exp_range': (0, 3),
        'publications_range': (0, 2),
        'preferences': {
            'research_focused': 0.7,
            'internship': 0.8,
            'work_visa': 0.6
        },
        'top_universities': ['MIT', 'Stanford', 'CMU', 'Berkeley', 'Harvard', 'Oxford', 'Cambridge', 'ETH Zurich']
    },
    'research_focused': {
        'count': 50,  # Reduced from 100
        'gre_v_range': (155, 165),
        'gre_q_range': (160, 170),
        'gre_a_range': (4.0, 5.5),
        'gpa_range': (3.5, 4.0),
        'majors': ['Computer Science', 'Physics', 'Mathematics', 'Engineering'],
        'countries': ['USA', 'UK', 'Switzerland', 'Germany', 'Netherlands'],
        'budget_range': (30000, 60000),
        'work_exp_range': (0, 2),
        'publications_range': (2, 8),
        'preferences': {
            'research_focused': 0.9,
            'internship': 0.4,
            'work_visa': 0.5
        },
        'top_universities': ['MIT', 'Caltech', 'Princeton', 'ETH Zurich', 'Cambridge', 'Imperial College London']
    },
    'business_analytics': {
        'count': 60,  # Reduced from 120
        'gre_v_range': (155, 165),
        'gre_q_range': (160, 168),
        'gre_a_range': (4.0, 5.0),
        'gpa_range': (3.3, 3.8),
        'majors': ['Business Analytics', 'Data Science', 'Business,Management', 'Finance'],
        'countries': ['USA', 'UK', 'Singapore', 'Australia'],
        'budget_range': (35000, 75000),
        'work_exp_range': (1, 5),
        'publications_range': (0, 1),
        'preferences': {
            'research_focused': 0.3,
            'internship': 0.9,
            'work_visa': 0.8
        },
        'top_universities': ['Harvard', 'Stanford', 'Wharton', 'INSEAD', 'NUS', 'London Business School']
    },
    'engineering': {
        'count': 65,  # Reduced from 130
        'gre_v_range': (150, 160),
        'gre_q_range': (165, 170),
        'gre_a_range': (3.5, 5.0),
        'gpa_range': (3.2, 3.7),
        'majors': ['Mechanical Engineering', 'Electrical Engineering', 'Civil Engineering', 'Aerospace Engineering'],
        'countries': ['USA', 'Germany', 'Canada', 'Australia'],
        'budget_range': (25000, 50000),
        'work_exp_range': (0, 4),
        'publications_range': (0, 2),
        'preferences': {
            'research_focused': 0.5,
            'internship': 0.7,
            'work_visa': 0.7
        },
        'top_universities': ['MIT', 'Stanford', 'Georgia Tech', 'TU Munich', 'University of Toronto']
    },
    'budget_conscious': {
        'count': 75,  # Reduced from 150
        'gre_v_range': (145, 158),
        'gre_q_range': (155, 165),
        'gre_a_range': (3.0, 4.5),
        'gpa_range': (3.0, 3.5),
        'majors': ['Computer Science', 'Engineering', 'Business Analytics', 'Data Science'],
        'countries': ['Germany', 'Netherlands', 'Singapore', 'Canada'],
        'budget_range': (10000, 30000),
        'work_exp_range': (0, 3),
        'publications_range': (0, 1),
        'preferences': {
            'research_focused': 0.4,
            'internship': 0.6,
            'work_visa': 0.8
        },
        'top_universities': ['TU Munich', 'TU Delft', 'NUS', 'NTU', 'University of Toronto']
    },
    'uk_preference': {
        'count': 50,  # Reduced from 100
        'gre_v_range': (155, 165),
        'gre_q_range': (158, 168),
        'gre_a_range': (4.0, 5.5),
        'gpa_range': (3.4, 3.9),
        'majors': ['Computer Science', 'Finance', 'Business,Management', 'Engineering'],
        'countries': ['UK'],
        'budget_range': (30000, 60000),
        'work_exp_range': (0, 3),
        'publications_range': (0, 2),
        'preferences': {
            'research_focused': 0.5,
            'internship': 0.7,
            'work_visa': 0.9
        },
        'top_universities': ['Oxford', 'Cambridge', 'Imperial College London', 'UCL', 'Edinburgh']
    },
    'mid_tier': {
        'count': 75,  # Reduced from 150
        'gre_v_range': (145, 155),
        'gre_q_range': (150, 160),
        'gre_a_range': (3.0, 4.0),
        'gpa_range': (2.8, 3.3),
        'majors': ['Computer Science', 'Engineering', 'Business Analytics', 'Information Technology'],
        'countries': ['USA', 'Canada', 'Australia', 'UK'],
        'budget_range': (20000, 45000),
        'work_exp_range': (1, 5),
        'publications_range': (0, 1),
        'preferences': {
            'research_focused': 0.3,
            'internship': 0.8,
            'work_visa': 0.7
        },
        'top_universities': ['Northeastern', 'Boston University', 'USC', 'NYU', 'University of Melbourne']
    },
    'diverse': {
        'count': 50,  # Reduced from 100
        'gre_v_range': (150, 165),
        'gre_q_range': (155, 168),
        'gre_a_range': (3.5, 5.0),
        'gpa_range': (3.2, 3.7),
        'majors': ['Computer Science', 'Data Science', 'Business Analytics', 'Engineering', 'Finance'],
        'countries': ['USA', 'UK', 'Canada', 'Australia', 'Singapore', 'Germany', 'Netherlands'],
        'budget_range': (25000, 60000),
        'work_exp_range': (0, 4),
        'publications_range': (0, 3),
        'preferences': {
            'research_focused': 0.5,
            'internship': 0.7,
            'work_visa': 0.7
        },
        'top_universities': ['MIT', 'Stanford', 'Cambridge', 'NUS', 'TU Munich', 'Toronto']
    }
}

# First names
FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Carol', 'Kevin', 'Amanda', 'Brian', 'Dorothy', 'George', 'Melissa',
    'Timothy', 'Deborah', 'Ronald', 'Stephanie', 'Edward', 'Rebecca', 'Jason', 'Sharon',
    'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
    'Nicholas', 'Angela', 'Eric', 'Shirley', 'Jonathan', 'Anna', 'Stephen', 'Brenda',
    'Larry', 'Pamela', 'Justin', 'Emma', 'Scott', 'Nicole', 'Brandon', 'Helen',
    'Benjamin', 'Samantha', 'Samuel', 'Katherine', 'Raymond', 'Christine', 'Frank', 'Debra',
    'Patrick', 'Rachel', 'Alexander', 'Carolyn', 'Jack', 'Janet', 'Dennis', 'Catherine',
    'Jerry', 'Maria', 'Tyler', 'Heather', 'Aaron', 'Diane', 'Jose', 'Ruth'
]

# Last names
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young',
    'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
    'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
    'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
    'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson'
]

def generate_email(first_name, last_name, user_num):
    """Generate realistic email address"""
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'university.edu']
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}{user_num}"
    ]
    return f"{random.choice(formats)}@{random.choice(domains)}"

def get_random_value(range_tuple):
    """Get random value from range"""
    if isinstance(range_tuple[0], int):
        return random.randint(range_tuple[0], range_tuple[1])
    else:
        return round(random.uniform(range_tuple[0], range_tuple[1]), 1)

def filter_universities_by_profile(data, profile, user_prefs):
    """Filter universities that match user profile"""
    filtered = data.copy()
    
    # Filter by field
    if user_prefs['major']:
        filtered = filtered[filtered['program_fields'].str.contains(user_prefs['major'], case=False, na=False)]
    
    # Filter by countries
    if user_prefs['countries']:
        filtered = filtered[filtered['country'].isin(user_prefs['countries'])]
    
    # Filter by budget
    filtered = filtered[filtered['tuition_usd'] <= user_prefs['budget']]
    
    # Filter by GRE requirements (within reasonable range)
    filtered = filtered[
        (filtered['greV'] <= user_prefs['greV'] + 5) &
        (filtered['greQ'] <= user_prefs['greQ'] + 5)
    ]
    
    return filtered

def generate_user_and_searches(profile_name, profile_config, user_num):
    """Generate a user with realistic search history"""
    
    # Generate user details
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    email = generate_email(first_name, last_name, user_num)
    
    # Check if user already exists
    existing_user = db.users.find_one({'email': email})
    if existing_user:
        return None
    
    # Create user
    password = 'Password123'  # Same for all test users
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Random member since date (last 6 months)
    days_ago = random.randint(1, 180)
    member_since = datetime.utcnow() - timedelta(days=days_ago)
    
    user_data = {
        'name': f"{first_name} {last_name}",
        'email': email,
        'password': hashed_password,
        'role': 'user',
        'created_at': member_since
    }
    
    user_result = db.users.insert_one(user_data)
    user_id = str(user_result.inserted_id)
    
    print(f"Created user {user_num}: {email} ({profile_name})")
    
    # Generate 1-5 searches per user
    num_searches = random.randint(1, 5)
    
    for search_num in range(num_searches):
        # Generate search preferences based on profile
        preferences = {
            'greV': get_random_value(profile_config['gre_v_range']),
            'greQ': get_random_value(profile_config['gre_q_range']),
            'greA': get_random_value(profile_config['gre_a_range']),
            'cgpa': get_random_value(profile_config['gpa_range']),
            'ielts': round(random.uniform(6.5, 8.5), 1),
            'toefl': random.randint(90, 120),
            'major': random.choice(profile_config['majors']),
            'workExperience': get_random_value(profile_config['work_exp_range']),
            'publications': get_random_value(profile_config['publications_range']),
            'countries': random.sample(profile_config['countries'], k=min(len(profile_config['countries']), random.randint(1, 4))),
            'budget': get_random_value(profile_config['budget_range']),
            'universityType': random.choice(['Any', 'Public', 'Private']),
            'duration': random.choice(['Any', '1 year', '2 years']),
            'researchFocused': random.random() < profile_config['preferences']['research_focused'],
            'internshipOpportunities': random.random() < profile_config['preferences']['internship'],
            'postStudyWorkVisa': random.random() < profile_config['preferences']['work_visa']
        }
        
        # Search timestamp (random time after user creation)
        search_days_ago = random.randint(0, days_ago)
        search_timestamp = datetime.utcnow() - timedelta(days=search_days_ago, hours=random.randint(0, 23))
        
        # Create search history
        search_data = {
            'user_id': user_id,
            'timestamp': search_timestamp,
            'preferences': preferences
        }
        
        search_result = db.search_history.insert_one(search_data)
        search_id = search_result.inserted_id
        
        # Generate recommendations (10-15 universities)
        filtered_unis = filter_universities_by_profile(data, profile_config, preferences)
        
        if len(filtered_unis) > 0:
            # Select some from profile's top universities and some random
            num_recommendations = random.randint(10, 15)
            
            # Get top universities from profile
            top_unis = filtered_unis[filtered_unis['univName'].isin(profile_config['top_universities'])]
            
            # Mix top universities with random ones
            if len(top_unis) >= 5:
                selected_top = top_unis.sample(n=min(5, len(top_unis)))
                remaining = num_recommendations - len(selected_top)
                if remaining > 0 and len(filtered_unis) > len(selected_top):
                    other_unis = filtered_unis[~filtered_unis['univName'].isin(selected_top['univName'])]
                    if len(other_unis) > 0:
                        selected_others = other_unis.sample(n=min(remaining, len(other_unis)))
                        selected_unis = pd.concat([selected_top, selected_others])
                    else:
                        selected_unis = selected_top
                else:
                    selected_unis = selected_top
            else:
                selected_unis = filtered_unis.sample(n=min(num_recommendations, len(filtered_unis)))
            
            # Create recommendation documents
            recommendations = []
            for idx, (_, uni) in enumerate(selected_unis.iterrows()):
                # Calculate realistic match score based on profile similarity
                base_score = random.uniform(0.75, 0.99)
                
                # Boost for top universities
                if uni['univName'] in profile_config['top_universities']:
                    base_score = min(0.99, base_score + random.uniform(0.05, 0.15))
                
                rec_data = {
                    'search_id': search_id,
                    'user_id': user_id,
                    'university_name': uni['univName'],
                    'country': uni['country'],
                    'ranking': int(uni['ranking']) if pd.notna(uni['ranking']) else 999,
                    'tuition': float(uni['tuition_usd']) if pd.notna(uni['tuition_usd']) else 0,
                    'match_score': round(base_score, 3),
                    'timestamp': search_timestamp
                }
                recommendations.append(rec_data)
            
            if recommendations:
                db.recommendations.insert_many(recommendations)
                print(f"  → Search {search_num + 1}: {len(recommendations)} recommendations")
        
        # Update search history with recommendations
        db.search_history.update_one(
            {'_id': search_id},
            {'$set': {'recommendations': recommendations if 'recommendations' in locals() else []}}
        )
    
    return user_id

def main():
    """Main function to populate database"""
    print("=" * 60)
    print("POPULATING DATABASE WITH 500 USERS")
    print("=" * 60)
    
    # Clear existing test data (optional - comment out if you want to keep existing users)
    # print("\nClearing existing test data...")
    # db.users.delete_many({'email': {'$regex': '@'}})
    # db.search_history.delete_many({})
    # db.recommendations.delete_many({})
    
    total_users = 0
    user_counter = 0
    
    # Generate users for each profile
    for profile_name, profile_config in USER_PROFILES.items():
        print(f"\n{'=' * 60}")
        print(f"Generating {profile_config['count']} users for profile: {profile_name.upper()}")
        print(f"{'=' * 60}")
        
        for i in range(profile_config['count']):
            user_counter += 1
            try:
                result = generate_user_and_searches(profile_name, profile_config, user_counter)
                if result:
                    total_users += 1
            except Exception as e:
                print(f"Error creating user {user_counter}: {str(e)}")
                continue
    
    print(f"\n{'=' * 60}")
    print(f"✅ POPULATION COMPLETE!")
    print(f"{'=' * 60}")
    print(f"Total users created: {total_users}")
    print(f"Total searches: {db.search_history.count_documents({})}")
    print(f"Total recommendations: {db.recommendations.count_documents({})}")
    print(f"\n📊 User Distribution:")
    for profile_name, profile_config in USER_PROFILES.items():
        print(f"  - {profile_name}: {profile_config['count']} users")
    
    print(f"\n🔐 All users have password: 'Password123'")
    print(f"\n✅ Collaborative filtering is now ready!")
    print(f"   - Multiple user groups formed")
    print(f"   - No cold start issue")
    print(f"   - Similar users will get collaborative recommendations")

if __name__ == "__main__":
    main()
