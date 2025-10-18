# 🚀 Quick Start Guide

## Get Started in 3 Simple Steps!

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Server
```bash
cd server
python server.py
```

### Step 3: Open Your Browser
```
http://localhost:5000
```

---

## ✅ Verify Installation

After running the server, you should see:
```
Loading and preparing enhanced university data...
Loaded 25808 universities with columns: [...]
Data segmentation complete!
 * Running on http://127.0.0.1:5000
```

---

## 🎯 Using the Application

1. **Navigate to Home Page** → Click "Graduate College"
2. **Enter Your Profile**:
   - GRE Scores (Verbal, Quantitative, Analytical)
   - CGPA/GPA
   - Language scores (IELTS/TOEFL)
   - Budget range
   - Country preference
   - Special preferences
3. **Click Submit** → Get your top 5 personalized university recommendations!

---

## 🔗 Quick Links

- **Home**: http://localhost:5000
- **Graduate Search**: http://localhost:5000/graduate
- **Documentation**: See README.md

---

## ⚠️ Troubleshooting

### Issue: Port 5000 already in use
**Solution**: 
```bash
# Kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill -9
```

### Issue: Module not found error
**Solution**: 
```bash
pip install -r requirements.txt
```

### Issue: CSV file not found
**Solution**: 
Ensure `Enhanced_University_Data.csv` is in:
```
WebScraped_data/csv/Enhanced_University_Data.csv
```

---

## 💡 Tips for Best Results

✅ **Be Realistic**: Enter scores you actually have or expect to achieve
✅ **Broaden Filters**: If you get < 5 results, relax some constraints
✅ **Try Different Combinations**: Experiment with various preferences
✅ **Check Google Links**: Click the 🔍 icon to research each university

---

## 🎓 Sample Test Profile

Try this profile to see the system in action:

- **GRE Verbal**: 160
- **GRE Quantitative**: 165
- **GRE Analytical**: 4.5
- **CGPA**: 3.8
- **IELTS**: 7.5
- **Country**: Any
- **Budget**: $0 - $100,000
- **Ranking**: Any

Expected result: 5 top-tier universities perfectly matched to this profile!

---

**Need Help?** Open an issue on GitHub or check the full README.md

Happy University Hunting! 🎓✨
