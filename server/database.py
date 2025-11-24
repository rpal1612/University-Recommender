"""
MongoDB database connection and operations
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime
from bson.objectid import ObjectId
import bcrypt

class Database:
    """MongoDB database wrapper"""
    
    def __init__(self, uri, db_name):
        """Initialize database connection"""
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=30000, connectTimeoutMS=30000, socketTimeoutMS=30000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self._setup_collections()
            print(f"✓ Connected to MongoDB: {db_name}")
        except ConnectionFailure as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Setup collections and indexes"""
        # Users collection
        self.users = self.db.users
        self.users.create_index([('email', ASCENDING)], unique=True)
        self.users.create_index([('created_at', DESCENDING)])
        
        # Create default admin if doesn't exist
        self._create_default_admin()
        
        # Search history collection
        self.search_history = self.db.search_history
        self.search_history.create_index([('user_id', ASCENDING)])
        self.search_history.create_index([('timestamp', DESCENDING)])
        self.search_history.create_index([('user_id', ASCENDING), ('timestamp', DESCENDING)])
        
        # Recommendations collection (for collaborative filtering)
        self.recommendations = self.db.recommendations
        self.recommendations.create_index([('user_id', ASCENDING)])
        self.recommendations.create_index([('university_name', ASCENDING)])
        self.recommendations.create_index([('user_id', ASCENDING), ('university_name', ASCENDING)])
        
        # Wishlist collection
        self.wishlist = self.db.wishlist
        self.wishlist.create_index([('user_id', ASCENDING)])
        self.wishlist.create_index([('user_id', ASCENDING), ('university_name', ASCENDING)], unique=True)
    
    def _create_default_admin(self):
        """Create default admin account if it doesn't exist"""
        try:
            admin_email = 'admin@gmail.com'
            existing_admin = self.users.find_one({'email': admin_email})
            
            if not existing_admin:
                password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
                admin_doc = {
                    'email': admin_email,
                    'password_hash': password_hash,
                    'full_name': 'Admin',
                    'role': 'admin',
                    'created_at': datetime.utcnow(),
                    'last_login': None,
                    'total_searches': 0
                }
                self.users.insert_one(admin_doc)
                print("✓ Default admin account created (admin@gmail.com / admin)")
        except Exception as e:
            print(f"Note: Admin account setup: {e}")
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, email, password, full_name, role='user'):
        """Create a new user"""
        try:
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            user_doc = {
                'email': email.lower().strip(),
                'password_hash': password_hash,
                'full_name': full_name.strip(),
                'role': role,  # 'user' or 'admin'
                'created_at': datetime.utcnow(),
                'last_login': None,
                'total_searches': 0
            }
            
            result = self.users.insert_one(user_doc)
            return str(result.inserted_id)
        
        except DuplicateKeyError:
            raise ValueError("Email already registered")
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        user = self.users.find_one({'email': email.lower().strip()})
        
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            # Update last login
            self.users.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            return user
        
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            return self.users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return self.users.find_one({'email': email.lower().strip()})
    
    def update_user(self, user_id, update_data):
        """Update user information"""
        try:
            result = self.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    # ==================== SEARCH HISTORY OPERATIONS ====================
    
    def save_search(self, user_id, search_data, recommendations):
        """Save user search and recommendations"""
        try:
            search_doc = {
                'user_id': str(user_id),
                'timestamp': datetime.utcnow(),
                'search_params': {
                    'greV': search_data.get('greV'),
                    'greQ': search_data.get('greQ'),
                    'greA': search_data.get('greA'),
                    'cgpa': search_data.get('cgpa'),
                    'ielts': search_data.get('ielts'),
                    'toefl': search_data.get('toefl'),
                    'major': search_data.get('major'),
                    'work_experience': search_data.get('workExperience', 0),
                    'publications': search_data.get('publications', 0),
                    'countries': search_data.get('country'),
                    'budget_min': search_data.get('budgetMin'),
                    'budget_max': search_data.get('budgetMax'),
                    'university_type': search_data.get('universityType'),
                    'duration': search_data.get('duration'),
                    'research_focus': search_data.get('researchFocus', False),
                    'internship_opportunities': search_data.get('internshipOpportunities', False),
                    'work_visa': search_data.get('workVisa', False),
                    'preference_weights': {
                        'academic_prestige': search_data.get('academicWeight', 30),
                        'admission_chances': search_data.get('admissionWeight', 25),
                        'affordability': search_data.get('budgetWeight', 20),
                        'career_outcomes': search_data.get('careerWeight', 15),
                        'location_preference': search_data.get('locationWeight', 10)
                    }
                },
                'recommendations': recommendations,
                'num_results': len(recommendations)
            }
            
            result = self.search_history.insert_one(search_doc)
            
            # Update user's total searches count
            self.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'total_searches': 1}}
            )
            
            # Save individual recommendations for collaborative filtering
            self._save_recommendations(user_id, recommendations)
            
            return str(result.inserted_id)
        
        except Exception as e:
            print(f"Error saving search: {e}")
            return None
    
    def _save_recommendations(self, user_id, recommendations):
        """Save individual recommendations for collaborative filtering"""
        for rec in recommendations:
            rec_doc = {
                'user_id': str(user_id),
                'university_name': rec.get('name'),
                'country': rec.get('country'),
                'match_score': rec.get('score'),
                'ranking': rec.get('ranking'),
                'timestamp': datetime.utcnow()
            }
            
            # Upsert - update if exists, insert if not
            self.recommendations.update_one(
                {
                    'user_id': str(user_id),
                    'university_name': rec.get('name')
                },
                {'$set': rec_doc},
                upsert=True
            )
    
    def get_user_history(self, user_id, limit=100):
        """
        Get user's search history for statistics calculation
        (Internal use - not exposed to user interface)
        """
        try:
            history = list(self.search_history.find(
                {'user_id': str(user_id)}
            ).sort('timestamp', DESCENDING).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for item in history:
                item['_id'] = str(item['_id'])
            
            return history
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    # ==================== COLLABORATIVE FILTERING ====================
    
    def get_similar_users(self, user_id, limit=10):
        """Find users with similar search patterns"""
        try:
            # Get current user's recommended universities
            user_recs = list(self.recommendations.find({'user_id': str(user_id)}))
            user_universities = {rec['university_name'] for rec in user_recs}
            
            if not user_universities:
                return []
            
            # Find other users who have similar recommendations
            similar_users_data = []
            
            # Get all users except current
            all_users = self.users.find({'_id': {'$ne': ObjectId(user_id)}})
            
            for other_user in all_users:
                other_user_id = str(other_user['_id'])
                other_recs = list(self.recommendations.find({'user_id': other_user_id}))
                other_universities = {rec['university_name'] for rec in other_recs}
                
                if not other_universities:
                    continue
                
                # Calculate Jaccard similarity
                intersection = user_universities.intersection(other_universities)
                union = user_universities.union(other_universities)
                
                if len(union) > 0:
                    similarity = len(intersection) / len(union)
                    
                    if similarity > 0:  # Only include users with some overlap
                        similar_users_data.append({
                            'user_id': other_user_id,
                            'similarity': similarity,
                            'common_universities': list(intersection),
                            'num_common': len(intersection)
                        })
            
            # Sort by similarity
            similar_users_data.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_users_data[:limit]
        
        except Exception as e:
            print(f"Error finding similar users: {e}")
            return []
    
    def get_collaborative_recommendations(self, user_id, limit=10):
        """Get recommendations based on similar users"""
        try:
            similar_users = self.get_similar_users(user_id, limit=5)
            
            if not similar_users:
                return []
            
            # Get current user's universities
            user_recs = list(self.recommendations.find({'user_id': str(user_id)}))
            user_universities = {rec['university_name'] for rec in user_recs}
            
            # Collect recommendations from similar users
            collaborative_recs = {}
            
            for similar_user in similar_users:
                weight = similar_user['similarity']
                similar_user_recs = self.recommendations.find({
                    'user_id': similar_user['user_id']
                })
                
                for rec in similar_user_recs:
                    uni_name = rec['university_name']
                    
                    # Skip universities user has already seen
                    if uni_name in user_universities:
                        continue
                    
                    if uni_name not in collaborative_recs:
                        collaborative_recs[uni_name] = {
                            'name': uni_name,
                            'country': rec['country'],
                            'weighted_score': 0,
                            'count': 0
                        }
                    
                    collaborative_recs[uni_name]['weighted_score'] += rec['match_score'] * weight
                    collaborative_recs[uni_name]['count'] += 1
            
            # Calculate average weighted scores
            result = []
            for uni_name, data in collaborative_recs.items():
                avg_score = data['weighted_score'] / data['count'] if data['count'] > 0 else 0
                result.append({
                    'name': uni_name,
                    'country': data['country'],
                    'collaborative_score': avg_score,
                    'recommended_by': data['count']
                })
            
            # Sort by score
            result.sort(key=lambda x: x['collaborative_score'], reverse=True)
            
            return result[:limit]
        
        except Exception as e:
            print(f"Error getting collaborative recommendations: {e}")
            return []
    
    # ==================== STATISTICS ====================
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            total_searches = self.search_history.count_documents({'user_id': str(user_id)})
            total_universities = self.recommendations.count_documents({'user_id': str(user_id)})
            
            # Get most searched countries
            pipeline = [
                {'$match': {'user_id': str(user_id)}},
                {'$group': {
                    '_id': '$country',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 5}
            ]
            top_countries = list(self.recommendations.aggregate(pipeline))
            
            return {
                'total_searches': total_searches,
                'unique_universities': total_universities,
                'top_countries': [{'country': item['_id'], 'count': item['count']} 
                                 for item in top_countries],
                'member_since': user.get('created_at'),
                'last_search': None  # Will be populated from history
            }
        
        except Exception as e:
            print(f"Error getting stats: {e}")
            return None
    
    # ==================== ADMIN OPERATIONS ====================
    
    def get_all_users(self, skip=0, limit=100):
        """Get all users (admin only)"""
        try:
            users = list(self.users.find(
                {'role': 'user'}  # Exclude admins
            ).skip(skip).limit(limit).sort('created_at', DESCENDING))
            
            # Convert ObjectId to string and clean up fields
            for user in users:
                user['_id'] = str(user['_id'])
                # Remove password fields
                user.pop('password_hash', None)
                user.pop('password', None)
                # Ensure name field exists (use full_name if name doesn't exist)
                if 'name' not in user and 'full_name' in user:
                    user['name'] = user['full_name']
                elif 'name' not in user:
                    user['name'] = user.get('email', 'Unknown').split('@')[0]
            
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def get_all_users_with_stats(self):
        """Get all users with their statistics (admin only)"""
        try:
            users = self.get_all_users(limit=1000)
            
            for user in users:
                user_id = user['_id']
                stats = self.get_user_stats(user_id)
                user['stats'] = stats
            
            return users
        except Exception as e:
            print(f"Error getting users with stats: {e}")
            return []
    
    def get_user_collaborative_groups(self):
        """
        Advanced Business-Focused User Segmentation System
        Creates strategic user groups with detailed business insights and actionable intelligence
        """
        try:
            print("🔍 Initiating Advanced User Segmentation Analysis...")
            
            # Step 1: Comprehensive User Profile Analysis
            print("  📊 Step 1: Building comprehensive user profiles...")
            pipeline = [
                {'$group': {
                    '_id': '$user_id',
                    'countries': {'$addToSet': '$search_params.countries'},
                    'majors': {'$addToSet': '$search_params.major'},
                    'avg_cgpa': {'$avg': '$search_params.cgpa'},
                    'avg_gre_v': {'$avg': '$search_params.greV'},
                    'avg_gre_q': {'$avg': '$search_params.greQ'},
                    'avg_gre_a': {'$avg': '$search_params.greA'},
                    'ielts_scores': {'$push': '$search_params.ielts'},
                    'toefl_scores': {'$push': '$search_params.toefl'},
                    'work_exp': {'$avg': '$search_params.workExperience'},
                    'research_papers': {'$avg': '$search_params.publications'},
                    'universities': {'$push': '$recommendations'},
                    'search_count': {'$sum': 1},
                    'first_search': {'$min': '$timestamp'},
                    'last_search': {'$max': '$timestamp'},
                    'categories': {'$push': '$category'}
                }},
                {'$match': {'search_count': {'$gte': 1}}}
            ]
            
            user_profiles = {}
            for doc in self.search_history.aggregate(pipeline):
                user_id = doc['_id']
                
                # Extract and clean countries
                countries = set()
                for country_list in doc.get('countries', []):
                    if country_list:
                        if isinstance(country_list, list):
                            countries.update([c for c in country_list if c])
                        else:
                            countries.add(country_list)
                
                # Extract majors
                majors = set([m for m in doc.get('majors', []) if m])
                
                # Calculate average scores
                avg_cgpa = round(doc.get('avg_cgpa', 0) or 0, 2)
                avg_gre_v = round(doc.get('avg_gre_v', 0) or 0, 1)
                avg_gre_q = round(doc.get('avg_gre_q', 0) or 0, 1)
                avg_gre_total = round(avg_gre_v + avg_gre_q, 1)
                
                # Calculate engagement metrics
                search_count = doc.get('search_count', 0)
                days_active = (doc.get('last_search') - doc.get('first_search')).days if doc.get('last_search') and doc.get('first_search') else 0
                
                # Determine user category distribution
                categories = [c for c in doc.get('categories', []) if c]
                category_dist = {
                    'Safety': categories.count('Safety'),
                    'Target': categories.count('Target'),
                    'Reach': categories.count('Reach'),
                    'Long Shot': categories.count('Long Shot')
                }
                dominant_category = max(category_dist, key=category_dist.get) if category_dist else 'Unknown'
                
                # Extract university names from nested structure
                universities = set()
                for rec_list in doc.get('universities', []):
                    if isinstance(rec_list, list):
                        for rec in rec_list:
                            if isinstance(rec, dict) and 'university_name' in rec:
                                universities.add(rec['university_name'])
                
                user_profiles[user_id] = {
                    'countries': countries,
                    'majors': majors,
                    'avg_cgpa': avg_cgpa,
                    'avg_gre_v': avg_gre_v,
                    'avg_gre_q': avg_gre_q,
                    'avg_gre_total': avg_gre_total,
                    'work_exp': round(doc.get('work_exp', 0) or 0, 1),
                    'research_papers': round(doc.get('research_papers', 0) or 0, 1),
                    'universities': universities,
                    'search_count': search_count,
                    'days_active': days_active,
                    'engagement_score': round(search_count / max(days_active, 1), 2),
                    'category_preference': dominant_category,
                    'category_distribution': category_dist
                }
            
            # Step 1.5: Integrate Wishlist Data
            print("  💝 Analyzing wishlist preferences...")
            for user_id in user_profiles.keys():
                wishlist_items = self.get_wishlist(user_id)
                user_profiles[user_id]['wishlist_count'] = len(wishlist_items)
                user_profiles[user_id]['wishlist_countries'] = set([item.get('country') for item in wishlist_items if item.get('country')])
                user_profiles[user_id]['wishlist_avg_tuition'] = sum([item.get('tuition', 0) or 0 for item in wishlist_items]) / len(wishlist_items) if wishlist_items else 0
                user_profiles[user_id]['has_wishlist'] = len(wishlist_items) > 0
            
            print(f"  ✓ Analyzed {len(user_profiles)} user profiles")
            
            if len(user_profiles) == 0:
                return []
            
            # Step 2: Fetch User Details
            print("  👥 Step 2: Retrieving user information...")
            user_ids_obj = [ObjectId(uid) for uid in user_profiles.keys() if len(uid) == 24]
            users_cursor = self.users.find({'_id': {'$in': user_ids_obj}})
            
            users_dict = {}
            for user in users_cursor:
                uid = str(user['_id'])
                users_dict[uid] = {
                    'name': user.get('name', user.get('full_name', user.get('email', 'Unknown').split('@')[0])),
                    'email': user.get('email', 'unknown@email.com')
                }
            
            # Step 3: Intelligent Segmentation
            print("  🎯 Step 3: Creating strategic user segments...")
            
            segments = {
                # Academic Performance Segments
                'elite_scholars': {
                    'name': 'Elite Scholars',
                    'description': 'Top-tier students (CGPA ≥9.0, GRE ≥325) targeting Ivy League & Top 20 universities',
                    'business_value': 'High-value segment for premium partnerships, scholarship programs',
                    'marketing_strategy': 'Emphasize prestige, research opportunities, career outcomes',
                    'members': [],
                    'criteria': lambda p: p['avg_cgpa'] >= 9.0 and p['avg_gre_total'] >= 325,
                    'icon': '🏆'
                },
                'high_achievers': {
                    'name': 'High Achievers',
                    'description': 'Strong students (CGPA 8-9, GRE 310-325) targeting Top 50 universities',
                    'business_value': 'Large segment with high conversion potential',
                    'marketing_strategy': 'Focus on competitive admissions, financial aid, ROI',
                    'members': [],
                    'criteria': lambda p: 8.0 <= p['avg_cgpa'] < 9.0 and 310 <= p['avg_gre_total'] < 325,
                    'icon': '⭐'
                },
                'rising_stars': {
                    'name': 'Rising Stars',
                    'description': 'Moderate achievers (CGPA 7-8, GRE 300-310) with growth potential',
                    'business_value': 'Opportunity segment - responsive to guidance and support services',
                    'marketing_strategy': 'Highlight improvement programs, conditional admits, pathway programs',
                    'members': [],
                    'criteria': lambda p: 7.0 <= p['avg_cgpa'] < 8.0 and 300 <= p['avg_gre_total'] < 310,
                    'icon': '📈'
                },
                
                # Specialization Segments
                'tech_innovators': {
                    'name': 'Tech Innovators',
                    'description': 'CS/Engineering students with research experience seeking tech hubs (US, Canada, Germany)',
                    'business_value': 'High-demand field with strong placement rates',
                    'marketing_strategy': 'Emphasize FAANG placements, startup culture, tech ecosystem',
                    'members': [],
                    'criteria': lambda p: any(m in ['Computer Science', 'Engineering', 'Data Science', 'AI/ML'] for m in p['majors']) and p['research_papers'] > 0,
                    'icon': '💻'
                },
                'business_leaders': {
                    'name': 'Business Leaders',
                    'description': 'Business/Management students with work experience (2+ years)',
                    'business_value': 'Executive education, MBA programs - premium pricing segment',
                    'marketing_strategy': 'Focus on networking, leadership development, career pivots',
                    'members': [],
                    'criteria': lambda p: any(m in ['Business', 'Management', 'MBA', 'Finance'] for m in p['majors']) and p['work_exp'] >= 2,
                    'icon': '💼'
                },
                'research_scholars': {
                    'name': 'Research Scholars',
                    'description': 'PhD-track students with publications seeking research universities',
                    'business_value': 'Academic partnerships, fellowship programs',
                    'marketing_strategy': 'Highlight research funding, faculty mentorship, publication opportunities',
                    'members': [],
                    'criteria': lambda p: p['research_papers'] >= 2 or (p['research_papers'] >= 1 and p['avg_cgpa'] >= 8.5),
                    'icon': '🔬'
                },
                
                # Geographic Segments
                'us_dreamers': {
                    'name': 'US Dreamers',
                    'description': 'Students exclusively targeting US universities',
                    'business_value': 'Largest international market - high visa service demand',
                    'marketing_strategy': 'US visa guidance, OPT/CPT, post-study work opportunities',
                    'members': [],
                    'criteria': lambda p: 'United States' in p['countries'] and len(p['countries']) <= 2,
                    'icon': '🇺🇸'
                },
                'european_explorers': {
                    'name': 'European Explorers',
                    'description': 'Students targeting UK, Germany, Netherlands (often seeking affordable quality)',
                    'business_value': 'Growing segment - lower costs, shorter programs',
                    'marketing_strategy': 'Emphasize affordability, quality education, work permits',
                    'members': [],
                    'criteria': lambda p: any(c in ['United Kingdom', 'Germany', 'Netherlands', 'Sweden', 'France'] for c in p['countries']),
                    'icon': '🇪🇺'
                },
                'global_explorers': {
                    'name': 'Global Explorers',
                    'description': 'Students considering 5+ countries (flexible, opportunity-focused)',
                    'business_value': 'Open to suggestions - high conversion for diverse programs',
                    'marketing_strategy': 'Comparative analysis, scholarship opportunities, unique programs',
                    'members': [],
                    'criteria': lambda p: len(p['countries']) >= 5,
                    'icon': '🌍'
                },
                
                # Engagement Segments
                'power_users': {
                    'name': 'Power Users',
                    'description': 'Highly engaged users (10+ searches) actively comparing options',
                    'business_value': 'Conversion-ready - likely to finalize soon',
                    'marketing_strategy': 'Decision support tools, personalized consultations, urgency messaging',
                    'members': [],
                    'criteria': lambda p: p['search_count'] >= 10,
                    'icon': '🔥'
                },
                'cautious_researchers': {
                    'name': 'Cautious Researchers',
                    'description': 'Students with 5-10 searches over extended period (careful decision-makers)',
                    'business_value': 'Need nurturing - respond well to testimonials and data',
                    'marketing_strategy': 'Success stories, detailed comparisons, risk mitigation info',
                    'members': [],
                    'criteria': lambda p: 5 <= p['search_count'] < 10 and p['days_active'] > 7,
                    'icon': '🤔'
                },
                'early_explorers': {
                    'name': 'Early Explorers',
                    'description': 'New users (1-3 searches) in discovery phase',
                    'business_value': 'Top of funnel - build trust and engagement',
                    'marketing_strategy': 'Educational content, guides, webinars, free resources',
                    'members': [],
                    'criteria': lambda p: p['search_count'] <= 3,
                    'icon': '🌱'
                },
                
                # Strategy Segments
                'safety_seekers': {
                    'name': 'Safety Seekers',
                    'description': 'Risk-averse students primarily targeting Safety schools',
                    'business_value': 'Reliable conversions - need confidence building',
                    'marketing_strategy': 'Emphasize acceptance rates, security, guaranteed outcomes',
                    'members': [],
                    'criteria': lambda p: p['category_preference'] == 'Safety' and p['category_distribution'].get('Safety', 0) > 5,
                    'icon': '🛡️'
                },
                'ambitious_realists': {
                    'name': 'Ambitious Realists',
                    'description': 'Students balancing Target and Reach schools (strategic approach)',
                    'business_value': 'Ideal segment - balanced expectations',
                    'marketing_strategy': 'Portfolio building, balanced applications, strategic guidance',
                    'members': [],
                    'criteria': lambda p: p['category_distribution'].get('Target', 0) >= 3 and p['category_distribution'].get('Reach', 0) >= 2,
                    'icon': '⚖️'
                },
                'dream_chasers': {
                    'name': 'Dream Chasers',
                    'description': 'Aspirational students primarily targeting Reach/Long Shot schools',
                    'business_value': 'Need realistic counseling but high motivation',
                    'marketing_strategy': 'Profile strengthening, backup plans, holistic admissions support',
                    'members': [],
                    'criteria': lambda p: p['category_preference'] in ['Reach', 'Long Shot'] and (p['category_distribution'].get('Reach', 0) + p['category_distribution'].get('Long Shot', 0)) > 5,
                    'icon': '🚀'
                },
                
                # Budget-Based Segments
                'budget_conscious': {
                    'name': 'Budget-Conscious Shoppers',
                    'description': 'Students prioritizing affordability (avg tuition < $25k or low-cost wishlists)',
                    'business_value': 'Scholarship program opportunities, affordable university partnerships',
                    'marketing_strategy': 'Emphasize scholarships, financial aid, low-cost quality options',
                    'members': [],
                    'criteria': lambda p: p.get('wishlist_avg_tuition', 50000) < 25000 and p.get('has_wishlist', False),
                    'icon': '💰'
                },
                'premium_seekers': {
                    'name': 'Premium Program Seekers',
                    'description': 'Students willing to pay premium (avg tuition > $50k)',
                    'business_value': 'High-value counseling services, premium partnerships',
                    'marketing_strategy': 'Focus on exclusivity, outcomes, prestige, ROI analysis',
                    'members': [],
                    'criteria': lambda p: p.get('wishlist_avg_tuition', 0) > 50000 and p.get('has_wishlist', False),
                    'icon': '💎'
                },
                
                # Wishlist Engagement Segments
                'wishlist_active': {
                    'name': 'Wishlist-Driven Researchers',
                    'description': 'Students actively using wishlist (5+ items) - highly engaged',
                    'business_value': 'Conversion-ready segment, need application support services',
                    'marketing_strategy': 'Application deadlines, document prep, interview coaching, decision support',
                    'members': [],
                    'criteria': lambda p: p.get('wishlist_count', 0) >= 5,
                    'icon': '⭐'
                },
                'wishlist_starters': {
                    'name': 'Wishlist Explorers',
                    'description': 'Students beginning to shortlist (2-4 wishlisted universities)',
                    'business_value': 'Mid-funnel segment, building decision momentum',
                    'marketing_strategy': 'Comparison tools, additional recommendations, nurture engagement',
                    'members': [],
                    'criteria': lambda p: 2 <= p.get('wishlist_count', 0) < 5,
                    'icon': '📝'
                }
            }
            
            # Step 4: Create Dynamic Groups Based on Country + Major Combinations
            print("  🎲 Step 4: Creating dynamic groups by country and major...")
            
            # Create groups for EVERY country + major combination
            dynamic_segments = {}
            
            for user_id, profile in user_profiles.items():
                if user_id not in users_dict:
                    continue
                
                user_data = {
                    'id': user_id,
                    'name': users_dict[user_id]['name'],
                    'email': users_dict[user_id]['email'],
                    'cgpa': profile['avg_cgpa'],
                    'gre_total': profile['avg_gre_total'],
                    'gre_v': profile['avg_gre_v'],
                    'gre_q': profile['avg_gre_q'],
                    'work_exp': profile['work_exp'],
                    'papers': profile['research_papers'],
                    'searches': profile['search_count'],
                    'countries': list(profile['countries'])[:3],
                    'majors': list(profile['majors'])[:2],
                    'top_universities': sorted(list(profile['universities']))[:5],
                    'engagement': profile['engagement_score'],
                    'strategy': profile['category_preference']
                }
                
                # Create groups for EACH country the user searched for
                for country in profile['countries']:
                    for major in profile['majors']:
                        # Create unique key for this country+major combination
                        dynamic_key = f"{major}_{country}".lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('/', '_').replace('(', '').replace(')', '')
                        
                        # Initialize dynamic segment if it doesn't exist
                        if dynamic_key not in dynamic_segments:
                            dynamic_segments[dynamic_key] = {
                                'name': f'{major} in {country}',
                                'description': f'Students interested in {major} programs in {country}',
                                'business_value': 'Targeted segment for specific program-location combinations',
                                'marketing_strategy': f'Localized content for {major} programs in {country}',
                                'members': [],
                                'criteria': lambda p: True,
                                'icon': '🎯',
                                'country_preference': country,
                                'course_preference': major
                            }
                        
                        # Add user to this segment (avoid duplicates)
                        if not any(m['id'] == user_id for m in dynamic_segments[dynamic_key]['members']):
                            dynamic_segments[dynamic_key]['members'].append(user_data)
            
            # Merge dynamic segments into main segments dictionary
            segments.update(dynamic_segments)
            
            total_groups = len([s for s in segments.values() if len(s['members']) > 0])
            total_users = sum(len(s['members']) for s in segments.values())
            print(f"  ✅ Created {total_groups} groups covering {total_users} user assignments")
            
            # Step 5: Format Output with Business Intelligence
            print("  📋 Step 5: Generating business intelligence reports...")
            output_groups = []
            
            # Sort segments: predefined first, then dynamic by member count
            predefined_segments = {k: v for k, v in segments.items() if not k.startswith('dynamic_')}
            dynamic_segments = {k: v for k, v in segments.items() if k.startswith('dynamic_')}
            sorted_segments = {**predefined_segments, **dynamic_segments}
            
            for idx, (segment_key, segment) in enumerate(sorted_segments.items(), 1):
                if len(segment['members']) >= 2:  # Only segments with 2+ members
                    members = segment['members']
                    
                    # Calculate segment statistics
                    avg_cgpa = sum(m['cgpa'] for m in members) / len(members)
                    avg_gre = sum(m['gre_total'] for m in members) / len(members)
                    avg_engagement = sum(m['engagement'] for m in members) / len(members)
                    total_searches = sum(m['searches'] for m in members)
                    
                    # Get common characteristics
                    all_countries = []
                    all_majors = []
                    all_universities = []
                    for m in members:
                        all_countries.extend(m['countries'])
                        all_majors.extend(m['majors'])
                        all_universities.extend(m['top_universities'])
                    
                    from collections import Counter
                    top_countries = [item for item, count in Counter(all_countries).most_common(3)]
                    top_majors = [item for item, count in Counter(all_majors).most_common(3)]
                    top_universities = [item for item, count in Counter(all_universities).most_common(5)]
                    
                    # Determine primary country and course for filtering
                    # Use preset values from dynamic segments, fallback to calculated
                    primary_country = segment.get('country_preference') or (top_countries[0] if top_countries else 'Any')
                    primary_course = segment.get('course_preference') or (top_majors[0] if top_majors else 'General')
                    
                    # Determine score range from average CGPA
                    if avg_cgpa >= 8.5:
                        score_range = 'High (8.5+)'
                    elif avg_cgpa >= 7.0:
                        score_range = 'Medium (7-8.5)'
                    else:
                        score_range = 'Low (<7)'
                    
                    output_groups.append({
                        'group_id': idx,
                        'segment_key': segment_key,
                        'segment_name': f"{segment['icon']} {segment['name']}",
                        'description': segment['description'],
                        
                        # Fields for UI filtering (backward compatibility)
                        'country_preference': primary_country,
                        'course_preference': primary_course,
                        'score_range': score_range,
                        'size': len(members),
                        'group_avg_cgpa': round(avg_cgpa, 2),
                        'group_avg_gre': round(avg_gre, 1),
                        'common_universities': top_universities,
                        'members': sorted(members, key=lambda x: x['cgpa'], reverse=True),
                        
                        # Advanced business intelligence
                        'business_intelligence': {
                            'value_proposition': segment['business_value'],
                            'marketing_approach': segment['marketing_strategy'],
                            'conversion_potential': 'High' if len(members) >= 10 and avg_engagement > 1 else 'Medium' if len(members) >= 5 else 'Low',
                            'revenue_opportunity': 'Premium' if 'elite' in segment_key or 'business' in segment_key else 'Standard'
                        },
                        'segment_metrics': {
                            'size': len(members),
                            'avg_cgpa': round(avg_cgpa, 2),
                            'avg_gre': round(avg_gre, 1),
                            'avg_engagement_score': round(avg_engagement, 2),
                            'total_searches': total_searches,
                            'searches_per_user': round(total_searches / len(members), 1)
                        },
                        'common_characteristics': {
                            'top_countries': top_countries,
                            'top_majors': top_majors,
                            'top_universities': top_universities
                        },
                        'actionable_insights': self._generate_segment_insights(segment_key, members, avg_cgpa, avg_gre)
                    })
            
            # Sort by business priority: size × engagement × conversion potential
            def business_priority(group):
                size = group['segment_metrics']['size']
                engagement = group['segment_metrics']['avg_engagement_score']
                conversion = 3 if group['business_intelligence']['conversion_potential'] == 'High' else 2 if group['business_intelligence']['conversion_potential'] == 'Medium' else 1
                return size * engagement * conversion
            
            output_groups.sort(key=business_priority, reverse=True)
            
            print(f"  ✅ Generated {len(output_groups)} strategic user segments")
            return output_groups
        
        except Exception as e:
            print(f"❌ Error in user segmentation: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _generate_segment_insights(self, segment_key, members, avg_cgpa, avg_gre):
        """Generate actionable business insights for each segment"""
        insights = []
        
        # Segment-specific insights
        if 'elite' in segment_key:
            insights.append("🎯 Target for premium counseling packages ($2000+)")
            insights.append("🤝 Partner with Ivy League alumni for testimonials")
            insights.append("📧 Personalized outreach from senior counselors")
        elif 'high_achievers' in segment_key:
            insights.append("💰 Offer scholarship search services")
            insights.append("📊 Provide detailed ROI analysis and career outcomes")
            insights.append("🎓 Bundle with test prep for profile enhancement")
        elif 'rising_stars' in segment_key:
            insights.append("📚 Upsell test prep and profile building services")
            insights.append("🔄 Focus on improvement pathway programs")
            insights.append("💡 Highlight conditional admission opportunities")
        elif 'tech_innovators' in segment_key:
            insights.append("💻 Emphasize tech hub locations and FAANG recruitment")
            insights.append("🔬 Connect with research labs and internship programs")
            insights.append("🌟 Showcase startup opportunities and innovation centers")
        elif 'business_leaders' in segment_key:
            insights.append("👔 Premium pricing for executive education consulting")
            insights.append("🤝 Corporate partnerships and sponsored programs")
            insights.append("📈 ROI calculator and career pivot success stories")
        elif 'power_users' in segment_key:
            insights.append("⚡ High-priority follow-up - decision imminent")
            insights.append("📞 Schedule personalized consultation calls")
            insights.append("🎁 Offer limited-time decision support packages")
        elif 'early_explorers' in segment_key:
            insights.append("📖 Nurture with educational content and guides")
            insights.append("🎥 Invite to free webinars and Q&A sessions")
            insights.append("📧 Automated email sequence with valuable resources")
        
        # General insights based on metrics
        if avg_cgpa >= 8.5:
            insights.append(f"✨ High average CGPA ({avg_cgpa:.1f}) - competitive for top programs")
        if avg_gre >= 320:
            insights.append(f"📈 Strong GRE scores ({avg_gre:.0f}) - highlight test-optional alternatives")
        if len(members) >= 15:
            insights.append(f"👥 Large segment ({len(members)} users) - consider group webinar")
        if len(members) >= 30:
            insights.append(f"🎯 Critical mass achieved - launch targeted email campaign")
        
        return insights[:6]  # Return top 6 insights
    
    def get_system_statistics(self):
        """Get real-time dynamic system statistics (admin only)"""
        try:
            from datetime import timedelta
            now = datetime.utcnow()
            print(f"\n🔄 Fetching FRESH statistics at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Basic counts
            total_users = self.users.count_documents({'role': 'user'})
            total_searches = self.search_history.count_documents({})
            print(f"   📊 Total Users: {total_users}, Total Searches: {total_searches}")
            
            # Most popular universities (from actual searches)
            popular_unis = list(self.search_history.aggregate([
                {'$unwind': '$recommendations'},
                {'$group': {
                    '_id': '$recommendations.university_name',
                    'count': {'$sum': 1},
                    'avg_score': {'$avg': '$recommendations.match_score'}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))
            
            # Most popular countries (from user searches)
            popular_countries = list(self.search_history.aggregate([
                {'$unwind': '$search_params.countries'},
                {'$group': {
                    '_id': '$search_params.countries',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))
            
            # Activity trend - searches over last 7 days (DYNAMIC)
            activity_labels = []
            activity_data = []
            for i in range(6, -1, -1):  # Last 7 days
                day = now - timedelta(days=i)
                day_start = datetime(day.year, day.month, day.day)
                day_end = day_start + timedelta(days=1)
                count = self.search_history.count_documents({
                    'timestamp': {'$gte': day_start, '$lt': day_end}
                })
                activity_labels.append(day.strftime('%b %d'))  # Nov 22, etc.
                activity_data.append(count)
            
            # Today's activity
            today_start = datetime(now.year, now.month, now.day)
            today_searches = self.search_history.count_documents({
                'timestamp': {'$gte': today_start}
            })
            print(f"   📅 Today's Searches: {today_searches}")
            
            # This week's activity
            week_start = now - timedelta(days=7)
            week_searches = self.search_history.count_documents({
                'timestamp': {'$gte': week_start}
            })
            
            # Active users (searched in last 24 hours)
            day_ago = now - timedelta(days=1)
            active_users = len(self.search_history.distinct('user_id', {
                'timestamp': {'$gte': day_ago}
            }))
            
            # Most popular majors/fields
            popular_majors = list(self.search_history.aggregate([
                {'$group': {
                    '_id': '$search_params.major',
                    'count': {'$sum': 1}
                }},
                {'$match': {'_id': {'$ne': None, '$ne': ''}}},
                {'$sort': {'count': -1}},
                {'$limit': 5}
            ]))
            
            # Average GRE and CGPA from recent searches
            recent_profiles = list(self.search_history.aggregate([
                {'$match': {'timestamp': {'$gte': week_start}}},
                {'$group': {
                    '_id': None,
                    'avg_cgpa': {'$avg': '$search_params.cgpa'},
                    'avg_gre_v': {'$avg': '$search_params.greV'},
                    'avg_gre_q': {'$avg': '$search_params.greQ'}
                }}
            ]))
            
            avg_profile = recent_profiles[0] if recent_profiles else {}
            avg_cgpa = round(avg_profile.get('avg_cgpa', 0) or 0, 2)
            avg_gre_v = round(avg_profile.get('avg_gre_v', 0) or 0, 1)
            avg_gre_q = round(avg_profile.get('avg_gre_q', 0) or 0, 1)
            avg_gre_total = round(avg_gre_v + avg_gre_q, 1)
            
            # New vs returning users this week
            week_user_ids = self.search_history.distinct('user_id', {
                'timestamp': {'$gte': week_start}
            })
            
            new_users_this_week = 0
            returning_users_this_week = 0
            for user_id in week_user_ids:
                first_search = self.search_history.find_one(
                    {'user_id': user_id},
                    sort=[('timestamp', 1)]
                )
                if first_search and first_search['timestamp'] >= week_start:
                    new_users_this_week += 1
                else:
                    returning_users_this_week += 1
            
            # Peak hour analysis (for last 7 days)
            hour_distribution = [0] * 24
            for search in self.search_history.find({'timestamp': {'$gte': week_start}}, {'timestamp': 1}):
                hour = search['timestamp'].hour
                hour_distribution[hour] += 1
            
            peak_hour = hour_distribution.index(max(hour_distribution)) if max(hour_distribution) > 0 else 12
            
            # Conversion metrics
            total_recommendations = sum(activity_data)  # Total from last 7 days
            avg_recs_per_search = round(total_recommendations / max(sum(activity_data), 1), 1) if sum(activity_data) > 0 else 15
            
            return {
                # Core metrics
                'total_users': total_users,
                'total_searches': total_searches,
                'today_searches': today_searches,
                'week_searches': week_searches,
                'active_users_24h': active_users,
                'new_users_week': new_users_this_week,
                'returning_users_week': returning_users_this_week,
                
                # User profile averages
                'avg_user_cgpa': avg_cgpa,
                'avg_user_gre': avg_gre_total,
                'avg_gre_verbal': avg_gre_v,
                'avg_gre_quant': avg_gre_q,
                
                # Popular data
                'popular_universities': [
                    {
                        'name': item['_id'] or 'Unknown',
                        'count': item['count'],
                        'avg_score': round(item['avg_score'], 2) if item['avg_score'] is not None else 0.0
                    }
                    for item in popular_unis if item['_id']
                ],
                'popular_countries': [
                    {'country': item['_id'] or 'Unknown', 'count': item['count']}
                    for item in popular_countries if item['_id']
                ],
                'popular_majors': [
                    {'major': item['_id'], 'count': item['count']}
                    for item in popular_majors
                ],
                
                # Activity trends (REAL-TIME)
                'activity_trend': {
                    'labels': activity_labels,
                    'data': activity_data
                },
                
                # Engagement metrics
                'avg_recs_per_search': avg_recs_per_search,
                'peak_hour': f"{peak_hour:02d}:00",
                'engagement_rate': round((active_users / max(total_users, 1)) * 100, 1),
                
                # System info
                'db_size': '27K unis',
                'last_updated': now.strftime('%b %d, %Y %H:%M UTC')
            }
        
        except Exception as e:
            print(f"Error getting system stats: {e}")
            import traceback
            traceback.print_exc()
            # Return empty stats
            return {
                'total_users': 0,
                'total_searches': 0,
                'today_searches': 0,
                'week_searches': 0,
                'active_users_24h': 0,
                'new_users_week': 0,
                'returning_users_week': 0,
                'avg_user_cgpa': 0,
                'avg_user_gre': 0,
                'avg_gre_verbal': 0,
                'avg_gre_quant': 0,
                'popular_universities': [],
                'popular_countries': [],
                'popular_majors': [],
                'activity_trend': {'labels': [], 'data': []},
                'avg_recs_per_search': 15,
                'peak_hour': '12:00',
                'engagement_rate': 0,
                'db_size': '27K unis',
                'last_updated': datetime.utcnow().strftime('%b %d, %Y %H:%M UTC')
            }
    
    # ==================== WISHLIST OPERATIONS ====================
    
    def add_to_wishlist(self, user_id, university_data):
        """Add university to user's wishlist"""
        try:
            wishlist_doc = {
                'user_id': str(user_id),
                'university_name': university_data['name'],
                'country': university_data.get('country'),
                'ranking': university_data.get('ranking'),
                'tuition': university_data.get('tuition_value'),
                'match_score': university_data.get('score'),
                'added_at': datetime.utcnow()
            }
            
            # Upsert - prevent duplicates
            self.wishlist.update_one(
                {
                    'user_id': str(user_id),
                    'university_name': university_data['name']
                },
                {'$set': wishlist_doc},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding to wishlist: {e}")
            return False
    
    def remove_from_wishlist(self, user_id, university_name):
        """Remove university from wishlist"""
        try:
            result = self.wishlist.delete_one({
                'user_id': str(user_id),
                'university_name': university_name
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error removing from wishlist: {e}")
            return False
    
    def get_wishlist(self, user_id):
        """Get user's wishlist"""
        try:
            wishlist = list(self.wishlist.find(
                {'user_id': str(user_id)}
            ).sort('added_at', DESCENDING))
            
            # Convert ObjectId to string
            for item in wishlist:
                item['_id'] = str(item['_id'])
            
            return wishlist
        except Exception as e:
            print(f"Error getting wishlist: {e}")
            return []
    
    def is_in_wishlist(self, user_id, university_name):
        """Check if university is in wishlist"""
        try:
            return self.wishlist.count_documents({
                'user_id': str(user_id),
                'university_name': university_name
            }) > 0
        except Exception as e:
            print(f"Error checking wishlist: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")
