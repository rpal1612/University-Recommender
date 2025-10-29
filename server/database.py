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
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
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
                    'work_visa': search_data.get('workVisa', False)
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
    
    def get_user_history(self, user_id, limit=10):
        """Get user's search history"""
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
    
    def get_search_by_id(self, search_id):
        """Get specific search by ID"""
        try:
            search = self.search_history.find_one({'_id': ObjectId(search_id)})
            if search:
                search['_id'] = str(search['_id'])
            return search
        except:
            return None
    
    def delete_search(self, user_id, search_id):
        """Delete a search from history"""
        try:
            result = self.search_history.delete_one({
                '_id': ObjectId(search_id),
                'user_id': str(user_id)
            })
            return result.deleted_count > 0
        except:
            return False
    
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
        """Group users by collaborative filtering similarity (admin only) - Optimized version"""
        try:
            print("Building collaborative groups (optimized)...")
            
            # Step 1: Get all users with their universities in one query
            print("  Step 1: Fetching user-university mappings...")
            pipeline = [
                {'$group': {
                    '_id': '$user_id',
                    'universities': {'$addToSet': '$university_name'}
                }},
                {'$match': {'universities': {'$ne': []}}},  # Only users with recommendations
                {'$limit': 500}  # Limit for performance
            ]
            
            user_unis = {}
            for doc in self.recommendations.aggregate(pipeline):
                user_unis[doc['_id']] = set(doc['universities'])
            
            print(f"  Found {len(user_unis)} users with recommendations")
            
            if len(user_unis) == 0:
                print("  No users with recommendations found")
                return []
            
            # Step 2: Get user details for these users only
            print("  Step 2: Fetching user details...")
            user_ids = list(user_unis.keys())
            users_cursor = self.users.find({'_id': {'$in': [ObjectId(uid) for uid in user_ids if len(uid) == 24]}})
            
            users_dict = {}
            for user in users_cursor:
                uid = str(user['_id'])
                users_dict[uid] = {
                    '_id': uid,
                    'name': user.get('name', user.get('full_name', user.get('email', 'Unknown').split('@')[0])),
                    'email': user.get('email', 'unknown@email.com')
                }
            
            print(f"  Loaded {len(users_dict)} user details")
            
            # Step 3: Build similarity matrix efficiently (only for users with >30% similarity)
            print("  Step 3: Calculating similarities...")
            groups = []
            processed = set()
            similarity_threshold = 0.25  # Lower threshold for better grouping
            
            user_list = list(user_unis.keys())
            
            for i, user_id in enumerate(user_list):
                if i % 100 == 0:
                    print(f"    Progress: {i}/{len(user_list)} users processed, {len(groups)} groups found")
                
                if user_id in processed:
                    continue
                
                user_universities = user_unis[user_id]
                if len(user_universities) == 0:
                    continue
                
                # Find similar users quickly
                group_members = [user_id]
                similarities = []
                
                # Only check remaining users
                for other_id in user_list[i+1:]:
                    if other_id in processed:
                        continue
                    
                    other_universities = user_unis[other_id]
                    if len(other_universities) == 0:
                        continue
                    
                    # Quick similarity check
                    intersection = user_universities & other_universities
                    if len(intersection) == 0:
                        continue
                    
                    union = user_universities | other_universities
                    similarity = len(intersection) / len(union)
                    
                    if similarity >= similarity_threshold:
                        group_members.append(other_id)
                        similarities.append({
                            'user_id': other_id,
                            'similarity': round(similarity, 3)
                        })
                
                # Create group if we found similar users
                if len(group_members) > 1:
                    processed.update(group_members)
                    
                    # Get user details
                    group_users = []
                    for uid in group_members:
                        if uid in users_dict:
                            group_users.append({
                                'id': uid,
                                'name': users_dict[uid]['name'],
                                'email': users_dict[uid]['email']
                            })
                    
                    groups.append({
                        'group_id': len(groups) + 1,
                        'members': group_users,
                        'size': len(group_users),
                        'avg_similarity': round(sum(s['similarity'] for s in similarities) / max(len(similarities), 1), 3),
                        'similarities': sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:3]
                    })
            
            print(f"  Step 4: Sorting and finalizing {len(groups)} groups")
            
            # Sort by size and limit
            groups.sort(key=lambda x: x['size'], reverse=True)
            top_groups = groups[:30]  # Show top 30 groups
            
            print(f"✓ Completed! Returning {len(top_groups)} collaborative groups")
            return top_groups
        
        except Exception as e:
            print(f"Error getting collaborative groups: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_system_statistics(self):
        """Get overall system statistics (admin only)"""
        try:
            total_users = self.users.count_documents({'role': 'user'})
            total_searches = self.search_history.count_documents({})
            total_recommendations = self.recommendations.count_documents({})
            
            # Most popular universities
            popular_unis = list(self.recommendations.aggregate([
                {'$group': {
                    '_id': '$university_name',
                    'count': {'$sum': 1},
                    'avg_score': {'$avg': '$match_score'}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))
            
            # Most popular countries
            popular_countries = list(self.recommendations.aggregate([
                {'$group': {
                    '_id': '$country',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))
            
            return {
                'total_users': total_users,
                'total_searches': total_searches,
                'total_recommendations': total_recommendations,
                'popular_universities': [
                    {'name': item['_id'], 'count': item['count'], 'avg_score': round(item['avg_score'], 2)}
                    for item in popular_unis
                ],
                'popular_countries': [
                    {'country': item['_id'], 'count': item['count']}
                    for item in popular_countries
                ]
            }
        
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return None
    
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
