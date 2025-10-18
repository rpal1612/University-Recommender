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

Choosing the right graduate university is one of the most critical decisions for students pursuing higher education. This intelligent recommendation system analyzes **25,808+ universities** worldwide and uses advanced machine learning algorithms to match students with their ideal graduate programs.

### **Key Highlights:**
- 🌍 **25,808 universities** from around the world
- 🤖 **Smart weighted scoring** algorithm (Academic 60%, Language 10%, Budget/Location 20%, Other factors 10%)
- 🎨 **Modern, responsive UI** with beautiful animations
- 🔍 **Dynamic filtering** by country, budget, ranking, type, and more
- 🔗 **Instant Google search** integration for each university
- ⚡ **Performance optimized** with data segmentation by GRE scores

---

## ✨ Features

### 🎓 **Academic Matching**
- GRE Verbal, Quantitative, and Analytical Writing scores
- Undergraduate CGPA/GPA consideration
- Intelligent similarity scoring based on your academic profile

### 🌐 **Advanced Filtering**
- **Country Selection**: USA, UK, Canada, Germany, Australia, or Any
- **Budget Range**: Customize minimum and maximum tuition fees
- **University Type**: Public, Private, or Both
- **World Ranking**: Filter by Top 50, 100, 200, 500, or Any
- **Program Duration**: 1 year or 2 years
- **Field of Study**: Computer Science, Engineering, Business, etc.

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

---

## 🧠 Algorithm & Methodology

### **Weighted Similarity Scoring System**

The recommendation engine uses a sophisticated **hybrid approach** combining K-Nearest Neighbors (KNN) with feature-weighted scoring:

#### **1. Data Segmentation (Performance Optimization)**
Universities are pre-segmented by total GRE scores for faster searching:
```
- Low (260-290): 911 universities
- Below Average (290-310): 4,294 universities
- Average (310-320): 6,428 universities
- Above Average (320-330): 9,147 universities
- High (330-340): 4,780 universities
- Excellent (340+): 248 universities
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
- If results < 5, expands search to adjacent GRE segments
- Ensures diverse recommendations with no duplicates

### **Algorithm Complexity**
- **Time Complexity**: O(n log n) where n = filtered universities
- **Space Complexity**: O(n) for score storage
- **Average Processing Time**: < 200ms for typical query

---

## 📊 Dataset

### **Source**
Graduate admission data scraped from **thegradcafe.com** - a comprehensive database of real student admissions data.

### **Statistics**
- **Total Universities**: 25,808
- **Coverage**: Global (USA, UK, Canada, Germany, Australia, etc.)
- **Data Points per University**: 16 features

### **Features**
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
- Budget range and country preference
- University type and ranking preference
- Special preferences (research/internship/visa)

![Graduate Input Page](/images/grad.png)

### **Step 3: View Recommendations**
Get your personalized top 5 university recommendations with:
- University name with Google search link 🔍
- Country and world ranking
- Tuition fees
- University type (Public/Private)
- Program duration
- Language requirements

![Recommendations Page](/images/graduate_recommendations.png)

### **Step 4: Research Universities**
Click the Google icon next to any university name to instantly search for more information, official websites, and admission details.

---

## 📁 Project Structure

```
University_Recommendation_System/
│
├── 📁 server/
│   └── server.py                    # Main Flask application
│
├── 📁 static/
│   ├── index.html                   # Home page
│   └── graduate.html                # Graduate search form
│
├── 📁 WebScraped_data/
│   └── 📁 csv/
│       └── Enhanced_University_Data.csv  # 25,808 universities dataset
│
└── README.md                        # This file
```

---

## 📸 Screenshots

### Home Page
![Home](/images/home.png)

### Graduate University Search
![Search Form](/images/grad.png)

### Personalized Recommendations
![Recommendations](/images/graduate_recommendations.png)

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
- Add more filtering options
- Implement user authentication
- Add university comparison feature
- Create data visualization dashboards
- Improve recommendation algorithm
- Add more international universities
- Implement saved searches
- Add email notifications

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




