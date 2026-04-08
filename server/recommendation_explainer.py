"""
Generate human-readable explanations for recommendations
"""

class RecommendationExplainer:
    """
    Generate detailed explanations for why universities are recommended
    """
    
    def generate_explanation(self, university_name, breakdown, category):
        """
        Generate comprehensive explanation
        Args:
            university_name: Name of the university
            breakdown: Score breakdown dictionary with component scores (0-1 scale)
            category: Category label (Safety/Target/Reach/Long Shot)
        """
        explanation = {
            'key_strengths': [],
            'considerations': [],
            'admission_insight': '',
            'financial_insight': ''
        }
        
        # Academic fit explanation
        academic_score = breakdown.get('academic_fit', 0.5) * 100
        if academic_score >= 85:
            explanation['key_strengths'].append(
                f"Excellent academic match - Your profile exceeds {university_name}'s typical requirements."
            )
        elif academic_score >= 70:
            explanation['key_strengths'].append(
                f"Your academic profile aligns excellently with {university_name}'s standards."
            )
        elif academic_score >= 60:
            explanation['considerations'].append(
                "Your academic profile meets most requirements. Highlight your strengths in your application."
            )
        else:
            explanation['considerations'].append(
                "Academic profile is below typical standards. Strong essays, recommendations, and relevant experience are crucial."
            )
        
        # Admission probability explanation with detailed guidance
        admission_prob = breakdown.get('admission_probability', 0.5) * 100
        
        if category == 'Safety':
            explanation['admission_insight'] = (
                f"<strong>{category}</strong> school with {admission_prob:.0f}% estimated admission probability. "
                f"You have a <strong>strong chance of admission</strong>. This is an excellent backup option. "
                f"Apply early to secure your spot and potentially qualify for merit scholarships."
            )
        elif category == 'Target':
            explanation['admission_insight'] = (
                f"<strong>{category}</strong> school with {admission_prob:.0f}% estimated admission probability. "
                f"<strong>You are a competitive candidate.</strong> Focus on crafting a compelling personal statement "
                f"that highlights your unique strengths and fit with the program."
            )
        elif category == 'Reach':
            explanation['admission_insight'] = (
                f"<strong>{category}</strong> school with {admission_prob:.0f}% estimated admission probability. "
                f"<strong>Competitive but achievable</strong> with a strong application. Emphasize unique experiences, "
                f"publications, and projects that differentiate you from other applicants."
            )
        else:
            explanation['admission_insight'] = (
                f"<strong>{category}</strong> school with {admission_prob:.0f}% estimated admission probability. "
                f"<strong>Highly selective</strong> option requiring exceptional credentials. Consider this as an aspirational choice "
                f"and ensure you have sufficient safety and target schools."
            )
        
        # Financial explanation with actionable advice
        financial_score = breakdown.get('financial_fit', 0.5) * 100
        if financial_score >= 90:
            explanation['financial_insight'] = "💰 Excellent financial fit - Tuition is well within your budget with room for living expenses."
        elif financial_score >= 75:
            explanation['financial_insight'] = "✅ Good financial fit - Tuition aligns well with your budget. Plan for additional costs like accommodation and materials."
        elif financial_score >= 60:
            explanation['financial_insight'] = "⚖️ Moderate fit - Tuition is manageable but tight. Strongly consider applying for teaching/research assistantships and departmental scholarships."
        elif financial_score >= 40:
            explanation['financial_insight'] = "⚠️ Financial stretch - Tuition exceeds budget. Essential to secure funding through scholarships, assistantships, or part-time work opportunities."
        else:
            explanation['financial_insight'] = "🔍 Outside budget - Explore external scholarships (Fulbright, DAAD, etc.), graduate assistantships, and employer sponsorships to make this feasible."
        
        # Career outcomes
        career_score = breakdown.get('career_outcomes', 0.5) * 100
        if career_score >= 75:
            explanation['key_strengths'].append(
                "Strong career placement outcomes and industry connections."
            )
        
        # Personal fit
        personal_score = breakdown.get('personal_fit', 0.5) * 100
        if personal_score >= 75:
            explanation['key_strengths'].append(
                "Excellent alignment with your personal preferences and goals."
            )
        
        return explanation
