# University Recommendation System - Scoring & Filtering Explanation

## Overview
The recommendation system uses a **comprehensive weighted scoring algorithm** that evaluates multiple factors to match students with universities. The total match score is a percentage (0-100%) representing how well a university fits your profile.

---

## 🎯 GRE Score Calculation & Academic Matching

### How GRE is Used (30% of Total Score)

The system calculates your **Academic Strength** using a normalized weighted formula:

```
Academic Strength = (GRE Verbal × 0.25) + (GRE Quant × 0.35) + (GRE Writing × 0.15) + (GPA × 0.25)
```

**Normalization Process:**
- GRE Verbal: (Your Score - 130) / 40  (converts 130-170 to 0-1 scale)
- GRE Quant: (Your Score - 130) / 40  (converts 130-170 to 0-1 scale)
- GRE Writing: Your Score / 6.0       (converts 0-6 to 0-1 scale)
- GPA: Your GPA / 4.0                 (converts 0-4 to 0-1 scale)

**Weight Breakdown:**
- **35%** - GRE Quantitative (most important for STEM fields)
- **25%** - GPA (second most important)
- **25%** - GRE Verbal
- **15%** - GRE Analytical Writing

### Example Calculation:
If you have:
- GRE Verbal: 160
- GRE Quant: 165
- GRE Writing: 4.0
- GPA: 3.8

```
Verbal Normalized: (160-130)/40 = 0.75
Quant Normalized: (165-130)/40 = 0.875
Writing Normalized: 4.0/6.0 = 0.667
GPA Normalized: 3.8/4.0 = 0.95

Academic Strength = (0.75 × 0.25) + (0.875 × 0.35) + (0.667 × 0.15) + (0.95 × 0.25)
                  = 0.1875 + 0.30625 + 0.10005 + 0.2375
                  = 0.831 (83.1% academic strength)
```

### Matching Logic:
1. **If your score ≥ university requirement**: Full academic match score (95-100%)
2. **If your score < university requirement**: Penalty applied (score reduced by 1.5× the gap)

This means:
- **Exceeding requirements** gives you maximum points
- **Meeting requirements** gives you high points
- **Below requirements** reduces your academic match score

---

## 📊 Complete Scoring Breakdown (100% Total)

### 1. Academic Match - 30%
- Based on GRE + GPA comparison with university requirements
- Uses the normalized academic strength formula above
- Universities with requirements similar to your profile score highest

### 2. University Prestige - 25%
- Based on university world ranking
- Better ranked universities (lower rank number) get higher prestige scores
- **Bonus modifiers:**
  - +5% if you have 3+ publications AND university is research-focused
  - +5% if you have 3+ years work experience AND university offers internships

### 3. Field Alignment - 20%
- Exact field match: 100% score
- Partial keyword match: 60-100% based on overlap
- No match: 20% (minimal credit)
- Example: If you select "Computer Science" and university offers "Computer Science, AI" → 100% match

### 4. Affordability - 15%
- Based on tuition vs your budget
- **Scoring:**
  - Within budget: Uses normalized affordability (cheaper = higher score)
  - Way below budget: 80% (might be suspiciously cheap)
  - Exceeds budget: Penalty (score reduces as overage increases)
  - Close to your budget midpoint: +15% bonus

### 5. Language Fit - 5%
- IELTS/TOEFL score vs university requirements
- Meeting requirements: 100%
- Exceeding requirements: 100%
- Below requirements: Penalty proportional to gap
- "Not Attempted": 50% (neutral score)

### 6. Preferences Alignment - 5%
- Research-focused preference match: +33.3%
- Internship opportunities match: +33.3%
- Post-study work visa match: +33.3%
- Duration match: Small bonus if matched

---

## 🔍 Filtering Process (Applied Before Scoring)

The system filters universities in this order:

### Step 1: Field of Study
- Only shows universities offering your selected field
- Uses case-insensitive partial matching
- Example: "Data Science" matches "Data Science, AI" and "Data Science, ML"

### Step 2: Country
- Filters by selected countries (can select multiple)
- Only universities in selected countries are shown

### Step 3: Budget
- Filters out universities with tuition outside your min-max budget range
- Universities with missing tuition data are included

### Step 4: University Type
- Public or Private filter
- "Any" shows both types

### Step 5: Duration ⚠️
- **1 Year Programs**: Only 1-year duration universities
- **2 Year Programs**: Only 2-year duration universities
- **Any Duration**: Shows all durations

**IMPORTANT NOTE:** The dataset currently has:
- **24,528** two-year programs (across all countries)
- **2,472** one-year programs (**ONLY in UK**)

**This means:**
- Selecting "1 Year Programs" + Any country except UK = **0 results**
- Selecting "1 Year Programs" + UK = Shows UK 1-year programs
- Australia, USA, Canada, Germany, etc. have **NO 1-year programs** in the current dataset

### Step 6: Additional Preferences
These are **soft filters** (don't eliminate universities, just boost matching scores):
- Research-Focused Programs
- Internship Opportunities
- Post-Study Work Visa

---

## 🎓 Example Recommendation Flow

**Your Profile:**
- GRE: V=155, Q=165, A=4.5
- GPA: 3.7
- Field: Computer Science
- Countries: USA, Canada
- Budget: $20,000 - $50,000
- Duration: 2 years

**What Happens:**

1. **Calculate Your Academic Strength:**
   ```
   Verbal: (155-130)/40 = 0.625
   Quant: (165-130)/40 = 0.875
   Writing: 4.5/6.0 = 0.75
   GPA: 3.7/4.0 = 0.925
   
   Strength = (0.625×0.25) + (0.875×0.35) + (0.75×0.15) + (0.925×0.25)
            = 0.156 + 0.306 + 0.113 + 0.231
            = 0.806 (80.6%)
   ```

2. **Filter Dataset:**
   - 27,000 total programs
   - Filter by "Computer Science" → ~5,000 programs
   - Filter by USA/Canada → ~2,000 programs
   - Filter by budget $20k-$50k → ~800 programs
   - Filter by 2-year duration → ~800 programs remain

3. **Score Each University:**
   For each of 800 universities, calculate:
   - Academic match (30%): Compare your 0.806 with each university's requirement
   - Prestige (25%): University ranking score
   - Field alignment (20%): How well CS matches their programs
   - Affordability (15%): How their tuition fits your budget
   - Language (5%): Your IELTS/TOEFL vs their requirement
   - Preferences (5%): Research/Internship/Visa matches

4. **Rank & Display:**
   - Sort all 800 universities by total score (highest first)
   - Show top results with match percentage
   - Remove duplicates (same university, different programs)
   - Display as filterable cards

---

## 💡 Tips for Better Results

### To Get More Results:
1. **Select "Any Duration"** instead of "1 Year Programs" (unless you specifically want UK programs)
2. **Increase budget range** to include more universities
3. **Select multiple countries** instead of just one
4. **Choose broader field categories** (e.g., "Engineering" instead of "Robotics, AI")

### To Get More Accurate Matches:
1. **Enter real GRE scores** - the algorithm heavily weights academic match
2. **Set realistic budget** based on your actual financial capacity
3. **Include work experience** if you have it (boosts scores for internship-focused programs)
4. **Add publications** if you have them (boosts scores for research universities)

### Understanding Match Percentages:
- **90-100%**: Excellent fit - You exceed requirements significantly
- **80-89%**: Very good fit - You meet or slightly exceed requirements
- **70-79%**: Good fit - You meet most requirements
- **60-69%**: Moderate fit - You're close to requirements
- **Below 60%**: Weak fit - Your profile doesn't align well

---

## 🐛 Known Dataset Limitations

1. **1-Year Programs**: Only available in UK (2,472 programs)
2. **Countries with data**: USA, UK, Canada, Australia, Germany, France, Singapore, Netherlands
3. **Total programs**: 27,000 (mix of different programs at 54 top universities)
4. **Some universities appear multiple times**: Same university with different program offerings

---

## 🔧 Technical Details

### Dataset Columns Used:
- `greV`, `greQ`, `greA`, `cgpa`: Student requirements
- `academic_strength`: Pre-calculated normalized strength for each program
- `ranking_score`: Inverted ranking (rank 1 = 1.0, rank 999 = ~0)
- `affordability`: Inverted tuition (cheaper = 1.0, expensive = 0)
- `research_flag`, `internship_flag`, `visa_flag`: Binary features
- `program_fields`: Available fields of study
- `duration_years`: Program duration (1 or 2)

### Preprocessing Applied:
All data has been cleaned and normalized with engineered features added for accurate predictions. Run `preprocess_dataset.py` to reapply preprocessing if dataset is replaced.

---

## Questions?

If you notice unexpected results:
1. Check the server console logs - they show filtering steps and score calculations
2. Verify your input values are realistic (GRE 130-170, GPA 0-4.0)
3. Remember: 1-year programs only exist in UK in current dataset
4. Budget must be in USD (not other currencies)

Last Updated: October 2025
