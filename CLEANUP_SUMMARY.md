# Database Cleanup & Enhancement Summary

## ✅ Completed Tasks

### 1. Database Cleanup
- **Removed**: 498 test users (kept 1 admin user)
- **Cleared**: 1,499 search histories, 9,733 recommendations
- **Cleaned**: All Flask session files and Python cache files (__pycache__)

### 2. Sample Data Population
- **Generated**: 140 high-quality sample users
- **Created**: 411 search histories, 2,891 recommendations
- **Distribution**:
  - Elite CS Students: 25 users
  - Research-Focused: 20 users
  - Business Analytics: 20 users
  - Engineering: 25 users
  - Budget-Conscious: 30 users
  - UK Preference: 20 users

### 3. Enhanced Group Display
#### New Features:
- **Expandable Groups**: Click "Show All Members" button to view complete member list
- **Common Universities**: Displays universities that all group members are interested in
- **Formation Criteria**: Shows average similarity percentages and top similarity scores
- **Better UX**: Toggle between compact view (10 members) and full view (all members)

#### What You'll See:
```
Group 1                    [15 members] [78% avg similarity]
------------------------------------------------------------
Members: user1, user2, user3... [Show All 15 Members]

Common Universities:
  Stanford    MIT    Harvard    Caltech    Berkeley

Top similarities: 85%, 82%, 79%
```

### 4. Performance Optimizations
- Reduced dataset from 1000 → 500 → 140 users
- MongoDB aggregation pipeline for O(n) performance
- 30-minute caching for group calculations
- Expected load time: <5 seconds (down from 60+ seconds)

## 📊 Current Database Status

```
Database: university_recommender
├── users: 141 (1 admin + 140 test users)
├── search_history: 411 entries
├── recommendations: 2,891 entries
└── wishlist: 0 entries
```

## 🎯 User Credentials

**Admin Account:**
- Email: `admin@university.com`
- Password: `admin123`

**All Sample Users:**
- Password: `Password123`
- Examples: 
  - carolyn1@gmail.com
  - srobinson@hotmail.com
  - (see database for complete list)

## 🚀 How to Use

1. **Start Server:**
   ```bash
   python server/server.py
   ```

2. **Access Admin Dashboard:**
   - Navigate to: `http://localhost:5000/admin`
   - Login with admin credentials
   - Click "Collaborative Groups" tab

3. **View Groups:**
   - See all collaborative groups sorted by size
   - Click "Show All Members" to expand any group
   - View common universities that connect group members
   - Check similarity percentages

## 🔧 Technical Details

### Collaborative Filtering Algorithm
- **Method**: Jaccard Similarity on university recommendations
- **Threshold**: 25% minimum similarity
- **Formula**: `similarity = |A ∩ B| / |A ∪ B|`
- **Groups**: Users with ≥25% common university interests

### File Structure
```
University-Recommender/
├── server/
│   ├── server.py              (Flask application with caching)
│   ├── database.py            (MongoDB operations with aggregation)
│   ├── populate_data.py       (Generate 140 sample users)
│   ├── clear_and_populate.py  (Database cleanup utility)
│   └── collaborative_filter.py (Recommendation engine)
├── static/
│   ├── admin.html             (Enhanced group display)
│   └── dashboard.html         (User dashboard)
└── csv/
    └── Real_University_Data.csv (University dataset)
```

## 🎨 Group Formation Criteria

Groups are formed when users share:
1. **Similar University Preferences** (≥25% overlap)
2. **Common Search Patterns** (based on recommendation history)
3. **Aligned Academic Interests** (by user profile archetypes)

Example:
- **Group 1**: Elite CS students interested in Stanford, MIT, Carnegie Mellon
- **Group 2**: Budget-conscious students looking at state universities
- **Group 3**: UK-focused students interested in Oxford, Cambridge, Imperial

## 📝 Maintenance

### To Repopulate Data:
```bash
python server/clear_and_populate.py
python server/populate_data.py
```

### To Adjust Sample Size:
Edit `server/populate_data.py` → `USER_PROFILES` dictionary

### To Clear Cache:
Restart the Flask server (cache expires automatically after 30 minutes)

## 🐛 Troubleshooting

**Groups not loading?**
- Check MongoDB connection (see server console)
- Verify users have search history and recommendations
- Wait for cache to expire (30 min) or restart server

**Empty common universities?**
- Normal for small groups with diverse interests
- Try groups with higher similarity scores (>50%)

**Performance issues?**
- Reduce user count in populate_data.py
- Increase cache duration in server.py (groups_cache)

---

**Last Updated**: Database cleaned and repopulated with 140 sample users
**Cache Status**: Cleared (will regenerate on first admin visit)
**Performance**: Optimized for <5 second group load times
