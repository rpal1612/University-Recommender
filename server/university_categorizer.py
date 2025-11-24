"""
Intelligent university categorization system
"""

class UniversityCategorizer:
    """
    Categorize universities for users: Safety, Target, Reach
    """
    
    def get_category(self, admission_probability):
        """
        Get category label based on admission probability (0-1)
        """
        prob_percent = admission_probability * 100 if admission_probability <= 1 else admission_probability
        
        if prob_percent >= 70:
            return 'Safety'
        elif prob_percent >= 50:
            return 'Target'
        elif prob_percent >= 30:
            return 'Reach'
        else:
            return 'Long Shot'
    
    def categorize_recommendations(self, universities_with_scores):
        """
        Categorize universities into Safety, Target, Reach, and Long Shot
        """
        categorized = {
            'safety': [],      # High admission probability (>70%)
            'target': [],      # Medium admission probability (50-70%)
            'reach': [],       # Lower admission probability (30-50%)
            'long_shot': []    # Very low admission probability (<30%)
        }
        
        for uni in universities_with_scores:
            admission_prob = uni['score_breakdown']['admission_probability']['score']
            
            if admission_prob >= 70:
                categorized['safety'].append(uni)
            elif admission_prob >= 50:
                categorized['target'].append(uni)
            elif admission_prob >= 30:
                categorized['reach'].append(uni)
            else:
                categorized['long_shot'].append(uni)
        
        return categorized
    
    def get_balanced_recommendations(self, categorized, total_count=15):
        """
        Return balanced mix: 40% safety, 40% target, 20% reach
        """
        safety_count = int(total_count * 0.4)
        target_count = int(total_count * 0.4)
        reach_count = total_count - safety_count - target_count
        
        balanced = []
        balanced.extend(categorized['safety'][:safety_count])
        balanced.extend(categorized['target'][:target_count])
        balanced.extend(categorized['reach'][:reach_count])
        
        # Fill remaining with best available
        if len(balanced) < total_count:
            remaining = total_count - len(balanced)
            for category in ['target', 'safety', 'reach', 'long_shot']:
                available = [u for u in categorized[category] if u not in balanced]
                balanced.extend(available[:remaining])
                if len(balanced) >= total_count:
                    break
        
        return balanced[:total_count]
    
    def get_category_summary(self, categorized):
        """
        Get summary statistics for each category
        """
        return {
            'safety': {
                'count': len(categorized['safety']),
                'description': 'High admission probability (>70%)',
                'recommendation': 'Strong chance of admission'
            },
            'target': {
                'count': len(categorized['target']),
                'description': 'Medium admission probability (50-70%)',
                'recommendation': 'Competitive candidate'
            },
            'reach': {
                'count': len(categorized['reach']),
                'description': 'Lower admission probability (30-50%)',
                'recommendation': 'Challenging but possible'
            },
            'long_shot': {
                'count': len(categorized['long_shot']),
                'description': 'Very low admission probability (<30%)',
                'recommendation': 'Highly competitive'
            }
        }
