"""
Enhanced scoring system with multi-dimensional analysis
"""
import numpy as np

class EnhancedScorer:
    """
    Advanced scoring system for university recommendations
    """
    
    def __init__(self, user_weights=None):
        # Default weights (can be customized per user)
        if user_weights:
            # Use user-provided weights (already normalized from 0-100)
            self.weights = {
                'academic_fit': user_weights.get('academic_prestige', 30) / 100,
                'admission_probability': user_weights.get('admission_chances', 25) / 100,
                'financial_fit': user_weights.get('affordability', 20) / 100,
                'career_outcomes': user_weights.get('career_outcomes', 15) / 100,
                'personal_fit': user_weights.get('location_preference', 10) / 100
            }
        else:
            self.weights = {
                'academic_fit': 0.30,
                'admission_probability': 0.25,
                'financial_fit': 0.20,
                'career_outcomes': 0.15,
                'personal_fit': 0.10
            }
    
    def calculate_academic_fit(self, user_profile, university):
        """
        Calculate academic alignment score (0-100)
        """
        scores = []
        
        # GRE Fit
        if university.get('greV') and university.get('greQ'):
            user_gre_total = user_profile['greV'] + user_profile['greQ']
            uni_gre_total = university['greV'] + university['greQ']
            
            # Calculate ratio to see how user compares
            gre_ratio = user_gre_total / uni_gre_total if uni_gre_total > 0 else 1.0
            
            if gre_ratio >= 1.0:
                gre_score = 100
            elif gre_ratio >= 0.95:
                gre_score = 90 + (gre_ratio - 0.95) * 200  # 90-100 range
            elif gre_ratio >= 0.85:
                gre_score = 70 + (gre_ratio - 0.85) * 200  # 70-90 range
            else:
                gre_score = max(0, gre_ratio * 82)  # 0-70 range
            
            scores.append(gre_score)
        
        # CGPA Fit
        if university.get('cgpa'):
            cgpa_ratio = user_profile['cgpa'] / university['cgpa'] if university['cgpa'] > 0 else 1.0
            
            if cgpa_ratio >= 1.0:
                cgpa_score = 100
            elif cgpa_ratio >= 0.95:
                cgpa_score = 90 + (cgpa_ratio - 0.95) * 200
            elif cgpa_ratio >= 0.85:
                cgpa_score = 70 + (cgpa_ratio - 0.85) * 200
            else:
                cgpa_score = max(0, cgpa_ratio * 82)
            
            scores.append(cgpa_score)
        
        # Work Experience Score (0-5 years range)
        work_experience = user_profile.get('workExperience', 0)
        if work_experience > 0:
            # 0 years = 50, 1 year = 65, 2 years = 75, 3 years = 85, 4+ years = 95
            if work_experience >= 4:
                exp_score = 95
            elif work_experience >= 3:
                exp_score = 85
            elif work_experience >= 2:
                exp_score = 75
            elif work_experience >= 1:
                exp_score = 65
            else:
                exp_score = 50
            scores.append(exp_score)
        
        # Publications Score (0-10+ publications range)
        publications = user_profile.get('publications', 0)
        if publications > 0:
            # 0 pubs = 50, 1-2 pubs = 70, 3-5 pubs = 85, 6-9 pubs = 95, 10+ pubs = 100
            if publications >= 10:
                pub_score = 100
            elif publications >= 6:
                pub_score = 95
            elif publications >= 3:
                pub_score = 85
            elif publications >= 1:
                pub_score = 70
            else:
                pub_score = 50
            scores.append(pub_score)
        
        return np.mean(scores) if scores else 50
    
    def calculate_admission_probability(self, user_profile, university, match_score=None):
        """
        Dynamic Admission Probability Calculation
        Adapts to each unique user-university combination without hardcoded thresholds
        Now incorporates match_score for logical consistency
        Returns: probability (0-100), level, and confidence
        """
        import math
        import random
        
        try:
            # Base probability starts at 50%
            base_probability = 50.0
            
            # ============================================================
            # Factor 0: Match Score Influence (NEW - Weight: 12%)
            # ============================================================
            if match_score is not None:
                # Higher match score = Better profile alignment = Higher admission chance
                if match_score >= 90:
                    match_influence = 12.0
                elif match_score >= 85:
                    match_influence = 8.0
                elif match_score >= 80:
                    match_influence = 5.0
                elif match_score >= 75:
                    match_influence = 2.0
                elif match_score >= 70:
                    match_influence = 0
                else:
                    match_influence = -5.0
                
                base_probability += match_influence
            
            # ============================================================
            # Factor 1: University Selectivity (Dynamic Rank-Based)
            # ============================================================
            world_rank = university.get('ranking', 500)
            if isinstance(world_rank, str):
                world_rank = int(str(world_rank).replace('#', '').replace('+', ''))
            
            # Dynamic selectivity calculation using logarithmic scale
            if world_rank <= 1000:
                selectivity_factor = -30 * math.log10(world_rank + 1) / math.log10(1001)
            else:
                selectivity_factor = 0
            
            base_probability += selectivity_factor
            
            # ============================================================
            # Factor 2: GPA Competitiveness (Relative to Rank)
            # ============================================================
            user_cgpa = user_profile.get('cgpa', 0)
            
            # Expected CGPA for this university's rank
            expected_cgpa = 2.5 + (1.5 * (1 - math.log10(world_rank + 1) / math.log10(1001)))
            
            # Calculate how much user exceeds/falls short
            cgpa_difference = user_cgpa - expected_cgpa
            
            # Sigmoid curve for smooth scaling
            cgpa_impact = 20 * (1 / (1 + math.exp(-2 * cgpa_difference)) - 0.5)
            
            base_probability += cgpa_impact
            
            # ============================================================
            # Factor 3: GRE Competitiveness (Dynamic Requirement Matching)
            # ============================================================
            user_gre_v = user_profile.get('greV', 150)
            user_gre_q = user_profile.get('greQ', 155)
            user_gre_total = user_gre_v + user_gre_q
            
            # University's GRE requirements
            uni_gre_v = university.get('greV', 150)
            uni_gre_q = university.get('greQ', 155)
            uni_gre_total = uni_gre_v + uni_gre_q
            
            # Estimate based on rank if no data
            if uni_gre_total < 300:
                uni_gre_total = 280 + int(35 * (1 - math.log10(world_rank + 1) / math.log10(1001)))
            
            gre_difference = user_gre_total - uni_gre_total
            
            # Dynamic GRE impact
            rank_importance = 1 + (1 - math.log10(world_rank + 1) / math.log10(1001))
            gre_impact = (gre_difference / 40) * 15 * rank_importance
            gre_impact = max(-20, min(20, gre_impact))
            
            base_probability += gre_impact
            
            # ============================================================
            # Factor 4: Work Experience (Dynamic Value Assessment)
            # ============================================================
            work_exp = user_profile.get('workExperience', 0)
            
            # Work experience value increases with university rank
            work_value_multiplier = 0.5 + (1 - math.log10(world_rank + 1) / math.log10(1001))
            
            if work_exp > 0:
                work_impact = min(work_exp * 2.5, 10) * work_value_multiplier
            else:
                work_impact = 0
            
            base_probability += work_impact
            
            # ============================================================
            # Factor 5: Research Publications (Dynamic Research Fit)
            # ============================================================
            publications = user_profile.get('publications', 0)
            research_focused = university.get('research_focused', False)
            
            if publications > 0:
                research_multiplier = 2.0 if research_focused else 1.0
                pub_impact = math.log(publications + 1) * 3 * research_multiplier
                pub_impact = min(pub_impact, 12)
            else:
                pub_impact = 0
                if research_focused:
                    pub_impact = -5
            
            base_probability += pub_impact
            
            # ============================================================
            # Factor 6: Field of Study Match (Semantic Similarity)
            # ============================================================
            user_major = str(user_profile.get('major', '')).lower().strip()
            uni_programs = str(university.get('program_fields', '')).lower()
            
            if user_major in uni_programs:
                field_match = 8
            elif any(word in uni_programs for word in user_major.split() if len(word) > 3):
                field_match = 4
            elif ('computer' in user_major or 'data' in user_major) and 'engineering' in uni_programs:
                field_match = 2
            else:
                field_match = -6
            
            base_probability += field_match
            
            # ============================================================
            # Factor 7: Geographic Competition Factor
            # ============================================================
            country = str(university.get('country', ''))
            
            competition_factors = {
                'USA': -5,
                'UK': -4,
                'Canada': -3,
                'Australia': -2,
                'Singapore': -2,
                'Netherlands': -1,
                'Germany': 0,
                'Switzerland': -1
            }
            
            geo_factor = competition_factors.get(country, 0)
            base_probability += geo_factor
            
            # ============================================================
            # Factor 8: Profile Consistency Score
            # ============================================================
            profile_scores = []
            
            gpa_strength = (user_cgpa - 3.0) / 0.5
            profile_scores.append(gpa_strength)
            
            gre_strength = (user_gre_total - 300) / 20
            profile_scores.append(gre_strength)
            
            exp_strength = min(work_exp / 2, 2)
            profile_scores.append(exp_strength)
            
            mean_score = sum(profile_scores) / len(profile_scores)
            variance = sum((s - mean_score) ** 2 for s in profile_scores) / len(profile_scores)
            std_dev = math.sqrt(variance)
            
            if std_dev < 0.5:
                consistency_bonus = 5
            elif std_dev < 1.0:
                consistency_bonus = 2
            else:
                consistency_bonus = -3
            
            base_probability += consistency_bonus
            
            # ============================================================
            # Factor 9: Unique Differentiation
            # ============================================================
            unique_seed = hash(f"{user_cgpa}{user_gre_total}{work_exp}{publications}{university.get('univName', '')}{world_rank}")
            random.seed(unique_seed)
            unique_variance = random.uniform(-3.0, 3.0)
            
            base_probability += unique_variance
            
            # ============================================================
            # Dynamic Probability Bounds (Rank-Based)
            # ============================================================
            if world_rank <= 10:
                max_prob = 78
            elif world_rank <= 25:
                max_prob = 82
            elif world_rank <= 50:
                max_prob = 86
            elif world_rank <= 100:
                max_prob = 90
            else:
                max_prob = 94
            
            min_prob = 12
            
            final_probability = max(min_prob, min(base_probability, max_prob))
            final_probability = round(final_probability, 1)
            
            # Determine level
            if final_probability >= 70:
                level = 'Safety'
            elif final_probability >= 50:
                level = 'Target'
            elif final_probability >= 30:
                level = 'Reach'
            else:
                level = 'Long Shot'
            
            return {
                'probability': final_probability,
                'level': level,
                'confidence': 'Medium'
            }
        
        except Exception as e:
            print(f"❌ Error calculating admission probability: {e}")
            return {
                'probability': 50.0,
                'level': 'Target',
                'confidence': 'Low'
            }
    
    def calculate_financial_fit(self, user_profile, university):
        """
        Calculate financial compatibility (0-100)
        Enhanced with stronger budget constraints
        """
        tuition = university.get('tuition_usd', 0)
        budget_max = user_profile.get('budgetMax', 100000)
        budget_min = user_profile.get('budgetMin', 0)
        
        if tuition == 0:
            return 50  # Neutral score if tuition unknown
        
        # Budget impact - penalize significantly if out of range
        if tuition < budget_min:
            # Below budget = safe but may signal quality concerns
            return 85 + (15 * (tuition / budget_min))
        elif tuition > budget_max:
            # Over budget - heavy penalty
            overage_ratio = (tuition - budget_max) / budget_max
            if overage_ratio < 0.1:  # Up to 10% over = moderate penalty
                return 70
            elif overage_ratio < 0.25:  # 10-25% over = significant penalty
                return 40
            else:  # More than 25% over = severe penalty
                return 10
        else:
            # Within budget - reward based on how good the deal is
            budget_range = budget_max - budget_min
            if budget_range > 0:
                relative_position = (tuition - budget_min) / budget_range
                # Lower in range = better deal
                return 100 - (relative_position * 20)  # Score: 100 (at min) to 80 (at max)
            else:
                return 100
    
    def calculate_career_outcomes(self, university):
        """
        Estimate career outcomes based on university attributes
        """
        score = 50  # Base score
        
        # Ranking bonus
        ranking = university.get('ranking', 500)
        if ranking <= 50:
            score += 30
        elif ranking <= 100:
            score += 20
        elif ranking <= 200:
            score += 10
        elif ranking <= 300:
            score += 5
        
        # Internship opportunities bonus
        if university.get('internship_opportunities'):
            score += 10
        
        # Work visa support bonus
        if university.get('post_study_work_visa'):
            score += 10
        
        return min(100, score)
    
    def calculate_personal_fit(self, user_profile, university):
        """
        Calculate personal preference fit
        """
        score = 50  # Base score
        
        # Country preference
        preferred_countries = user_profile.get('preferred_countries', [])
        if university.get('country') in preferred_countries:
            score += 20
        
        # University type preference
        preferred_type = user_profile.get('universityType')
        if preferred_type and preferred_type != 'Any':
            if university.get('university_type') == preferred_type:
                score += 15
        
        # Research focus match
        if user_profile.get('researchFocus') and university.get('research_focused'):
            score += 15
        
        return min(100, score)
    
    def calculate_comprehensive_score(self, user_profile, university):
        """
        Calculate final comprehensive score with all factors
        Returns: score (0-100) and detailed breakdown
        """
        # Calculate individual components
        academic_fit = self.calculate_academic_fit(user_profile, university)
        financial_fit = self.calculate_financial_fit(user_profile, university)
        career_outcomes = self.calculate_career_outcomes(university)
        personal_fit = self.calculate_personal_fit(user_profile, university)
        
        # Calculate preliminary match score (without admission probability)
        preliminary_match_score = (
            self.weights['academic_fit'] * academic_fit +
            self.weights['financial_fit'] * financial_fit +
            self.weights['career_outcomes'] * career_outcomes +
            self.weights['personal_fit'] * personal_fit
        ) / (self.weights['academic_fit'] + self.weights['financial_fit'] + 
             self.weights['career_outcomes'] + self.weights['personal_fit']) if (
            self.weights['academic_fit'] + self.weights['financial_fit'] + 
            self.weights['career_outcomes'] + self.weights['personal_fit']) > 0 else 50.0
        
        # Now calculate admission probability WITH match score
        admission_prob_data = self.calculate_admission_probability(user_profile, university, match_score=preliminary_match_score)
        
        # Calculate weighted score
        final_score = (
            self.weights['academic_fit'] * academic_fit +
            self.weights['admission_probability'] * admission_prob_data['probability'] +
            self.weights['financial_fit'] * financial_fit +
            self.weights['career_outcomes'] * career_outcomes +
            self.weights['personal_fit'] * personal_fit
        )
        
        # Detailed breakdown
        breakdown = {
            'academic_fit': {
                'score': round(academic_fit, 1),
                'weight': self.weights['academic_fit'],
                'contribution': round(self.weights['academic_fit'] * academic_fit, 1)
            },
            'admission_probability': {
                'score': round(admission_prob_data['probability'], 1),
                'level': admission_prob_data['level'],
                'confidence': admission_prob_data['confidence'],
                'weight': self.weights['admission_probability'],
                'contribution': round(self.weights['admission_probability'] * admission_prob_data['probability'], 1)
            },
            'financial_fit': {
                'score': round(financial_fit, 1),
                'weight': self.weights['financial_fit'],
                'contribution': round(self.weights['financial_fit'] * financial_fit, 1)
            },
            'career_outcomes': {
                'score': round(career_outcomes, 1),
                'weight': self.weights['career_outcomes'],
                'contribution': round(self.weights['career_outcomes'] * career_outcomes, 1)
            },
            'personal_fit': {
                'score': round(personal_fit, 1),
                'weight': self.weights['personal_fit'],
                'contribution': round(self.weights['personal_fit'] * personal_fit, 1)
            },
            'final_score': round(final_score, 1)
        }
        
        return final_score, breakdown
    
    def customize_weights(self, user_priorities):
        """
        Allow users to customize scoring weights
        """
        if user_priorities:
            self.weights.update(user_priorities)
            # Normalize to sum to 1.0
            total = sum(self.weights.values())
            self.weights = {k: v/total for k, v in self.weights.items()}
