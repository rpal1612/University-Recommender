"""
Collaborative filtering for hybrid recommendations
Combines content-based filtering with collaborative filtering
"""
import numpy as np
from collections import defaultdict

class CollaborativeFilter:
    """Collaborative filtering engine"""
    
    def __init__(self, database, weight=0.3):
        """
        Initialize collaborative filter
        
        Args:
            database: Database instance
            weight: Weight for collaborative score (0-1), default 0.3 = 30% collaborative, 70% content
        """
        self.db = database
        self.collaborative_weight = weight
        self.content_weight = 1 - weight
    
    def get_hybrid_recommendations(self, user_id, content_based_results, limit=15):
        """
        Get hybrid recommendations combining content-based and collaborative filtering
        
        Args:
            user_id: Current user ID
            content_based_results: List of universities from content-based filtering
            limit: Maximum number of results
        
        Returns:
            List of universities with hybrid scores
        """
        try:
            # Get collaborative recommendations
            collaborative_recs = self.db.get_collaborative_recommendations(user_id, limit=20)
            
            if not collaborative_recs:
                # No collaborative data, return content-based results
                return content_based_results[:limit]
            
            # Create lookup for collaborative scores
            collab_scores = {
                rec['name']: rec['collaborative_score'] 
                for rec in collaborative_recs
            }
            
            # Normalize content-based scores (0-100 scale)
            if content_based_results:
                max_content_score = max(uni.get('score', 0) for uni in content_based_results)
                min_content_score = min(uni.get('score', 0) for uni in content_based_results)
                score_range = max_content_score - min_content_score if max_content_score != min_content_score else 1
            else:
                score_range = 1
            
            # Calculate hybrid scores
            hybrid_results = []
            
            for uni in content_based_results:
                uni_name = uni.get('name')
                content_score = uni.get('score', 0)
                
                # Normalize content score to 0-100
                normalized_content = ((content_score - min_content_score) / score_range) * 100 if score_range > 0 else content_score
                
                # Get collaborative score if available
                collab_score = collab_scores.get(uni_name, 0)
                
                # Calculate hybrid score
                if collab_score > 0:
                    hybrid_score = (
                        self.content_weight * normalized_content + 
                        self.collaborative_weight * collab_score
                    )
                    uni['has_collaborative'] = True
                else:
                    # No collaborative data for this university, use only content score
                    hybrid_score = normalized_content
                    uni['has_collaborative'] = False
                
                uni['hybrid_score'] = round(hybrid_score, 2)
                uni['content_score'] = round(normalized_content, 2)
                uni['collaborative_score'] = round(collab_score, 2)
                
                hybrid_results.append(uni)
            
            # Add universities that are highly recommended collaboratively but not in content results
            content_uni_names = {uni['name'] for uni in content_based_results}
            
            for collab_rec in collaborative_recs[:5]:  # Top 5 collaborative recommendations
                if collab_rec['name'] not in content_uni_names:
                    # This is a new recommendation from collaborative filtering
                    hybrid_score = self.collaborative_weight * collab_rec['collaborative_score']
                    
                    hybrid_results.append({
                        'name': collab_rec['name'],
                        'country': collab_rec['country'],
                        'hybrid_score': round(hybrid_score, 2),
                        'content_score': 0,
                        'collaborative_score': round(collab_rec['collaborative_score'], 2),
                        'has_collaborative': True,
                        'collaborative_only': True,
                        'recommended_by_users': collab_rec['recommended_by']
                    })
            
            # Sort by hybrid score
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return hybrid_results[:limit]
        
        except Exception as e:
            print(f"Error in hybrid recommendations: {e}")
            # Fallback to content-based results
            return content_based_results[:limit]
    
    def calculate_user_similarity(self, user1_id, user2_id):
        """
        Calculate similarity between two users using Jaccard similarity
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
        
        Returns:
            Similarity score (0-1)
        """
        try:
            # Get recommendations for both users
            user1_recs = list(self.db.recommendations.find({'user_id': str(user1_id)}))
            user2_recs = list(self.db.recommendations.find({'user_id': str(user2_id)}))
            
            # Extract university names
            user1_unis = {rec['university_name'] for rec in user1_recs}
            user2_unis = {rec['university_name'] for rec in user2_recs}
            
            if not user1_unis or not user2_unis:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(user1_unis.intersection(user2_unis))
            union = len(user1_unis.union(user2_unis))
            
            return intersection / union if union > 0 else 0.0
        
        except Exception as e:
            print(f"Error calculating user similarity: {e}")
            return 0.0
    
    def calculate_university_popularity(self, university_name):
        """
        Calculate how popular a university is based on recommendations
        
        Args:
            university_name: Name of the university
        
        Returns:
            Popularity score (number of users who received this recommendation)
        """
        try:
            count = self.db.recommendations.count_documents({
                'university_name': university_name
            })
            return count
        except Exception as e:
            print(f"Error calculating popularity: {e}")
            return 0
    
    def get_trending_universities(self, limit=10, days=30):
        """
        Get trending universities based on recent recommendations
        
        Args:
            limit: Number of universities to return
            days: Consider recommendations from last N days
        
        Returns:
            List of trending universities
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Aggregate trending universities
            pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff_date}}},
                {'$group': {
                    '_id': '$university_name',
                    'count': {'$sum': 1},
                    'avg_score': {'$avg': '$match_score'},
                    'countries': {'$addToSet': '$country'}
                }},
                {'$sort': {'count': -1}},
                {'$limit': limit}
            ]
            
            trending = list(self.db.recommendations.aggregate(pipeline))
            
            result = []
            for item in trending:
                result.append({
                    'name': item['_id'],
                    'recommendation_count': item['count'],
                    'average_score': round(item['avg_score'], 2),
                    'countries': item['countries']
                })
            
            return result
        
        except Exception as e:
            print(f"Error getting trending universities: {e}")
            return []
    
    def get_recommendations_for_similar_users(self, user_id, limit=10):
        """
        Get universities recommended to similar users that current user hasn't seen
        
        Args:
            user_id: Current user ID
            limit: Number of recommendations
        
        Returns:
            List of recommended universities
        """
        try:
            # Find similar users
            similar_users = self.db.get_similar_users(user_id, limit=5)
            
            if not similar_users:
                return []
            
            # Get current user's universities
            user_recs = list(self.db.recommendations.find({'user_id': str(user_id)}))
            user_unis = {rec['university_name'] for rec in user_recs}
            
            # Collect recommendations from similar users
            recommendations = defaultdict(lambda: {
                'score': 0,
                'count': 0,
                'similarity_sum': 0
            })
            
            for similar_user in similar_users:
                similarity = similar_user['similarity']
                similar_user_recs = self.db.recommendations.find({
                    'user_id': similar_user['user_id']
                })
                
                for rec in similar_user_recs:
                    uni_name = rec['university_name']
                    
                    # Skip if user has already seen
                    if uni_name in user_unis:
                        continue
                    
                    recommendations[uni_name]['score'] += rec['match_score'] * similarity
                    recommendations[uni_name]['count'] += 1
                    recommendations[uni_name]['similarity_sum'] += similarity
                    recommendations[uni_name]['country'] = rec['country']
            
            # Calculate average scores
            result = []
            for uni_name, data in recommendations.items():
                avg_score = data['score'] / data['similarity_sum'] if data['similarity_sum'] > 0 else 0
                result.append({
                    'name': uni_name,
                    'country': data['country'],
                    'predicted_score': round(avg_score, 2),
                    'recommended_by': data['count']
                })
            
            # Sort by predicted score
            result.sort(key=lambda x: x['predicted_score'], reverse=True)
            
            return result[:limit]
        
        except Exception as e:
            print(f"Error getting similar user recommendations: {e}")
            return []
    
    def explain_recommendation(self, user_id, university_name):
        """
        Explain why a university was recommended
        
        Args:
            user_id: User ID
            university_name: University name
        
        Returns:
            Explanation dictionary
        """
        try:
            # Check if user has this recommendation
            user_rec = self.db.recommendations.find_one({
                'user_id': str(user_id),
                'university_name': university_name
            })
            
            if not user_rec:
                return {'error': 'Recommendation not found'}
            
            # Get similar users who also got this recommendation
            similar_users = self.db.get_similar_users(user_id)
            similar_with_uni = []
            
            for similar_user in similar_users:
                similar_rec = self.db.recommendations.find_one({
                    'user_id': similar_user['user_id'],
                    'university_name': university_name
                })
                
                if similar_rec:
                    similar_with_uni.append({
                        'similarity': similar_user['similarity'],
                        'score': similar_rec['match_score']
                    })
            
            # Calculate popularity
            popularity = self.calculate_university_popularity(university_name)
            
            return {
                'university': university_name,
                'your_match_score': user_rec.get('match_score'),
                'popularity': popularity,
                'similar_users_count': len(similar_with_uni),
                'similar_users_avg_score': round(
                    np.mean([u['score'] for u in similar_with_uni]), 2
                ) if similar_with_uni else 0,
                'explanation': f"Recommended based on your profile (match score: {user_rec.get('match_score')}) "
                             f"and {len(similar_with_uni)} similar users who also matched with this university."
            }
        
        except Exception as e:
            print(f"Error explaining recommendation: {e}")
            return {'error': str(e)}
