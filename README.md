# 🎓 Graduate University Recommendation System

> An intelligent, AI-powered recommendation system that helps students find their perfect graduate school matches based on academic profile, preferences, and weighted similarity algorithms.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [Algorithm & Methodology](#-algorithm--methodology)
- [Dataset](#-dataset)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)
- [Technologies Used](#-technologies-used)
- [Contributing](#-contributing)

---

## 🎯 Overview

Choosing the right graduate university is one of the most critical decisions for students pursuing higher education. This intelligent recommendation system demonstrates an AI-powered approach to university matching using **weighted similarity algorithms** and **multi-criteria filtering**.

### **Key Highlights:**
- 🤖 **Smart weighted scoring** algorithm (Academic 60%, Language 10%, Budget/Location 20%, Other factors 10%)
- 🎨 **Modern, responsive UI** with beautiful animations and fallback recommendations
- 🔍 **Comprehensive filtering system** with 8 countries and multiple criteria
- 🔗 **Instant Google search** integration for each university
- ⚡ **Performance optimized** with data segmentation by GRE scores
- 🌍 **International coverage** with 54 top universities from 8 countries
- 💡 **Smart fallback system** - Shows alternative matches based on GRE & budget when strict criteria yield few results

**Real Data**: 27,000 entries covering top universities from USA, UK, Canada, Australia, Germany, Netherlands, Singapore, and Switzerland with diverse program options.

---

## ✨ Features

### 🎓 **Academic Matching**
- GRE Verbal, Quantitative, and Analytical Writing scores
- Undergraduate CGPA/GPA consideration
- Intelligent similarity scoring based on your academic profile

### 🌐 **Advanced Filtering**
- **Country Selection**: USA, UK, Canada, Germany, Australia, Netherlands, Singapore, Switzerland, or Any
- **Budget Range**: $1,500 - $60,000+ (supports affordable European universities)
- **University Type**: Public, Private, or Both
- **World Ranking**: Filter by Top 50, 100, 200, 500, or Any
- **Program Duration**: 1 year (mostly UK) or 2 years
- **Field of Study**: Computer Science, Engineering, Business, Data Science, Mathematics, Physics, and more

### 🎯 **Smart Preferences**
- Research-focused programs
- Internship opportunities
- Post-study work visa availability
- Language proficiency requirements (IELTS/TOEFL)

### 💼 **Professional Profile**
- Work experience consideration
- Research publications bonus
- Tailored recommendations based on career goals

### 🎨 **Beautiful User Experience**
- Modern gradient design with smooth animations
- Responsive layout for all devices
- Interactive university cards with hover effects
- One-click Google search for each university
- Real-time score visualization
- **Smart fallback recommendations** with visual distinction (orange badges for alternative matches)
- Clear messaging when showing results based on relaxed criteria

---

## 🧠 Algorithm & Methodology

### **Weighted Similarity Scoring System**

The recommendation engine uses a sophisticated **hybrid approach** combining K-Nearest Neighbors (KNN) with feature-weighted scoring:

#### **1. Data Segmentation (Performance Optimization)**
Universities are pre-segmented by total GRE scores for faster searching:
```
- Low (260-290): 0 universities
- Below Average (290-310): 1,292 universities
- Average (310-320): 9,379 universities
- Above Average (320-330): 12,209 universities
- High (330-340): 4,120 universities
- Excellent (340+): 0 universities
```

#### **2. Multi-Criteria Filtering**
Hard filters eliminate non-matching universities based on:
- Country preference
- Budget constraints
- University type
- Maximum world ranking
- Program duration
- Language requirements
- Special preferences (research/internship/visa)

#### **3. Weighted Similarity Score Calculation**

For each remaining university, a similarity score (0-1) is calculated:

**📊 Academic Match (60% weight)**
```python
similarity = 1 - (|user_score - uni_score| / score_range)
academic_score = avg(GRE_V_sim, GRE_Q_sim, GRE_W_sim, CGPA_sim) × 0.60
```

**🌐 Language Proficiency (10% weight)**
```python
language_score = 1 - (|user_score - uni_min| / max_score) × 0.10
```

**💰 Budget & Location (20% weight)**
```python
country_match = 1.0 if match else 0.3
budget_match = 1 - (|uni_tuition - budget_mid| / budget_mid)
location_score = (country_match + budget_match) / 2 × 0.20
```

**🏆 Other Factors (10% weight)**
```python
ranking_bonus = 1 - (ranking / 500)
experience_bonus = work_exp > 2 ? 0.2 : 0
publications_bonus = has_publications ? 0.2 : 0
preferences_bonus = matches(research, internship, visa)
other_score = sum(bonuses) × 0.10
```

**🎯 Final Score**
```python
Total_Score = academic_score + language_score + location_score + other_score
```

#### **4. Ranking & Selection**
- Universities sorted by total similarity score (descending)
- Top 5 unique universities selected
- **Smart Country Filter**: NEVER ignores country preference - always respects your selection
- **Intelligent Fallback**: If < 5 matches found with all criteria:
  - Shows perfect matches first (purple cards)
  - Adds alternative matches based on GRE scores & budget (orange cards with "Alternative Match" badge)
  - Clear messaging explains the distinction
- Ensures diverse recommendations with no duplicates

### **Algorithm Complexity**
- **Time Complexity**: O(n log n) where n = filtered universities
- **Space Complexity**: O(n) for score storage
- **Average Processing Time**: < 200ms for typical query

---

## 📊 Dataset

### **Current Data**
This project uses **real university data** with 54 top-ranked universities from 8 countries.

### **Statistics**
- **Total Entries**: 27,000
- **Unique Universities**: 54 (top-ranked institutions worldwide)
- **Countries**: USA, UK, Canada, Australia, Germany, Netherlands, Singapore, Switzerland
- **Program Durations**: 1-year and 2-year programs (UK offers both, others primarily 2-year)
- **Tuition Range**: $1,425 - $57,747 USD (includes affordable European options)
- **Data Points per Entry**: 16 features

### **✅ Data Coverage**
The current dataset (`Real_University_Data.csv`) includes:
- **8 countries** with diverse options
- **Both 1-year and 2-year** program durations
- **Wide tuition range** from affordable ($1,425 in Germany/Switzerland) to premium ($57,000+)
- **Top-ranked universities**: Stanford, MIT, Harvard, Oxford, Cambridge, ETH Zurich, TUM, and more
- **500 entries per university** for comprehensive matching

### **🌍 Country Distribution**
- **USA**: 10 universities (5,000 entries) - Stanford, MIT, Harvard, UC Berkeley, Princeton, CMU, Columbia, Cornell, UCLA, Michigan
- **UK**: 10 universities (5,000 entries) - Oxford, Cambridge, Imperial, UCL, Edinburgh, Manchester, King's College, LSE, Bristol, Warwick
- **Canada**: 10 universities (5,000 entries) - Toronto, UBC, McGill, McMaster, Alberta, Waterloo, Western, Queen's, Calgary, SFU
- **Australia**: 8 universities (4,000 entries) - Melbourne, ANU, Sydney, UNSW, Queensland, Monash, Western Australia, Adelaide
- **Germany**: 8 universities (4,000 entries) - TUM, LMU Munich, Heidelberg, Humboldt, RWTH Aachen, Freiburg, Bonn, TU Berlin
- **Netherlands**: 4 universities (2,000 entries) - Amsterdam, Delft, Leiden, Utrecht
- **Singapore**: 2 universities (1,000 entries) - NUS, NTU
- **Switzerland**: 2 universities (1,000 entries) - ETH Zurich, EPFL

### **Dataset Features**
| Feature | Description |
|---------|-------------|
| `univName` | University name |
| `greV` | Average GRE Verbal score (130-170) |
| `greQ` | Average GRE Quantitative score (130-170) |
| `greA` | Average GRE Analytical Writing score (0-6) |
| `cgpa` | Average undergraduate GPA (0-4.0) |
| `country` | Country location |
| `university_type` | Public or Private |
| `ranking` | QS World University Ranking |
| `tuition_usd` | Annual tuition in USD |
| `ielts_min` | Minimum IELTS requirement |
| `toefl_min` | Minimum TOEFL requirement |
| `duration_years` | Program duration (1 or 2 years) |
| `research_focused` | Research-oriented program |
| `internship_opportunities` | Internship availability |
| `post_study_work_visa` | Work visa availability |
| `program_fields` | Available fields of study |

---

## 🚀 Installation

### **Prerequisites**
- Python 3.12 or higher
- pip (Python package manager)

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/University_Recommendation_System.git
cd University_Recommendation_System
```

### **Step 2: Install Dependencies**
```bash
pip install flask pandas numpy scikit-learn markupsafe
```

### **Step 3: Run the Application**
```bash
cd server
python server.py
```

### **Step 4: Access the Application**
Open your browser and navigate to:
```
http://localhost:5000
```

🎉 **That's it! The application should now be running.**

---

## 💻 Usage

### **Step 1: Home Page**
Visit `http://localhost:5000` to see the welcome page.

![Home Page](/images/home.png)

### **Step 2: Enter Your Profile**
Click on "Graduate College" and fill in your details:
- GRE Verbal, Quantitative, and Analytical Writing scores
- Undergraduate CGPA
- Language test scores (IELTS/TOEFL)
- Major field of study
- Work experience and publications
- Budget range ($1,500 - $60,000+) and country preference (8 countries available)
- University type and ranking preference
- Special preferences (research/internship/visa)
- Program duration (1 or 2 years)

![Graduate Input Page](/images/grad.png)

### **Step 3: View Recommendations**
Get your personalized top 5 university recommendations with:
- University name with Google search link 🔍
- Country and world ranking
- Tuition fees
- University type (Public/Private)
- Program duration (1 or 2 years)
- Language requirements
- **Visual distinction**: 
  - Purple gradient cards = Perfect matches (all criteria met)
  - Orange gradient cards = Alternative matches (GRE & budget based) with "Alternative Match" badge

![Recommendations Page](/images/graduate_recommendations.png)

### **Step 4: Research Universities**
Click the Google icon next to any university name to instantly search for more information, official websites, and admission details.

---

## 📁 Project Structure

```
University_Recommendation_System/
│
├── 📁 server/
│   └── server.py                    # Main Flask application (53 KB)
│
├── 📁 static/
│   ├── index.html                   # Home page (8 KB)
│   └── graduate.html                # Graduate search form (23 KB)
│
├── 📁 WebScraped_data/
│   └── 📁 csv/
│       └── Real_University_Data.csv # 27,000 entries dataset (2.8 MB)
│
├── � README.md                     # Project documentation (12 KB)
├── 📄 QUICKSTART.md                 # Quick setup guide (2 KB)
├── 📄 LICENSE                       # MIT License (1 KB)
└── 📄 requirements.txt              # Python dependencies
```

---

## 📸 Screenshots

*Screenshots to be added - showing home page, search form, and recommendation results with the new fallback system featuring orange "Alternative Match" badges.*

---

## 🛠 Technologies Used

### **Backend**
- **Python 3.12** - Core programming language
- **Flask 3.0** - Web framework
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **scikit-learn** - Machine learning algorithms

### **Frontend**
- **HTML5** - Structure
- **CSS3** - Styling with gradients and animations
- **Bootstrap 4** - Responsive design
- **Font Awesome 6** - Icons
- **Google Fonts (Poppins)** - Typography

### **Data**
- **CSV** - Data storage
- **Web Scraping** - Data collection (thegradcafe.com)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### **Ideas for Contribution:**
- Add more universities and countries
- Implement user authentication and saved searches
- Add university comparison feature side-by-side
- Create data visualization dashboards (acceptance rates, trends)
- Improve recommendation algorithm with machine learning
- Add scholarship information
- Implement email notifications for deadlines
- Add program-specific filtering (MS, PhD, MBA)
- Integration with university application portals
- Add reviews and ratings from current students

---
## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---


