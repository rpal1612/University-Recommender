// University Recommender - Form JavaScript
// Created: October 19, 2025

// Load countries and fields dynamically on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCountries();
    loadFields();
    setupLanguageTestToggle();
    setupFormSubmission();
});

// Load countries dynamically from backend
async function loadCountries() {
    try {
        const response = await fetch('/api/countries');
        const countries = await response.json();
        const container = document.getElementById('countryCheckboxes');
        
        // Budget ranges by country
        const budgetRanges = {
            'Germany': { min: 2000, max: 5000 },
            'Switzerland': { min: 1000, max: 3000 },
            'Canada': { min: 15000, max: 30000 },
            'Netherlands': { min: 15000, max: 22000 },
            'UK': { min: 20000, max: 45000 },
            'Australia': { min: 30000, max: 50000 },
            'Singapore': { min: 30000, max: 40000 },
            'USA': { min: 25000, max: 65000 }
        };
        
        countries.forEach(country => {
            const div = document.createElement('div');
            div.className = 'country-checkbox-item';
            div.innerHTML = `
                <input type="checkbox" name="preferred_countries" value="${country}" id="country_${country}" onchange="updateBudgetHint()">
                <label for="country_${country}">${country}</label>
            `;
            container.appendChild(div);
        });
        
        // Store budget ranges globally for use in updateBudgetHint
        window.budgetRanges = budgetRanges;
        
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

// Load fields of study from backend
async function loadFields() {
    try {
        const response = await fetch('/api/fields');
        const fields = await response.json();
        const select = document.getElementById('major');
        
        // Clear existing options
        select.innerHTML = '<option value="">Select your field...</option>';
        
        fields.forEach(field => {
            const option = document.createElement('option');
            option.value = field;
            option.textContent = field;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading fields:', error);
        // Fallback to manual input if API fails
        console.log('Using fallback fields');
    }
}

// This function is replaced below with budget hint functionality

// Setup language test toggle (IELTS/TOEFL/Not Attempted)
function setupLanguageTestToggle() {
    const englishTest = document.getElementById('englishTest');
    const ieltsGroup = document.getElementById('ieltsGroup');
    const toeflGroup = document.getElementById('toeflGroup');
    const ieltsInput = document.querySelector('[name="ielts"]');
    const toeflInput = document.querySelector('[name="toefl"]');
    
    englishTest.addEventListener('change', function() {
        if (this.value === 'IELTS') {
            ieltsGroup.style.display = 'block';
            toeflGroup.style.display = 'none';
            toeflInput.value = '0';
            toeflInput.removeAttribute('required');
            ieltsInput.setAttribute('required', 'required');
        } else if (this.value === 'TOEFL') {
            ieltsGroup.style.display = 'none';
            toeflGroup.style.display = 'block';
            ieltsInput.value = '0';
            ieltsInput.removeAttribute('required');
            toeflInput.setAttribute('required', 'required');
        } else {
            // Not Attempted
            ieltsGroup.style.display = 'none';
            toeflGroup.style.display = 'none';
            ieltsInput.value = '0';
            toeflInput.value = '0';
            ieltsInput.removeAttribute('required');
            toeflInput.removeAttribute('required');
        }
    });
}

// Setup form submission
function setupFormSubmission() {
    const form = document.getElementById('recommendationForm');
    const loader = document.getElementById('loader');
    
    form.addEventListener('submit', function() {
        loader.classList.add('active');
    });
}

// Update budget hint based on selected countries
function updateBudgetHint() {
    const checkedCountries = Array.from(document.querySelectorAll('input[name="preferred_countries"]:checked'))
        .map(cb => cb.value);
    
    const budgetMinInput = document.querySelector('input[name="budgetMin"]');
    const budgetMaxInput = document.querySelector('input[name="budgetMax"]');
    
    if (checkedCountries.length > 0 && window.budgetRanges) {
        if (checkedCountries.length === 1) {
            // Single country - use specific range
            const country = checkedCountries[0];
            const range = window.budgetRanges[country];
            
            if (range) {
                budgetMinInput.value = range.min;
                budgetMaxInput.value = range.max;
                budgetMinInput.placeholder = `Suggested min: $${range.min.toLocaleString()}`;
                budgetMaxInput.placeholder = `Suggested max: $${range.max.toLocaleString()}`;
            }
        } else {
            // Multiple countries - use broader range
            let minOfMins = Math.min(...checkedCountries
                .filter(c => window.budgetRanges[c])
                .map(c => window.budgetRanges[c].min));
            let maxOfMaxs = Math.max(...checkedCountries
                .filter(c => window.budgetRanges[c])
                .map(c => window.budgetRanges[c].max));
            
            // If we have valid ranges, set broader budget
            if (minOfMins !== Infinity && maxOfMaxs !== -Infinity) {
                budgetMinInput.value = Math.max(0, minOfMins - 5000); // Slightly lower min
                budgetMaxInput.value = maxOfMaxs + 10000; // Slightly higher max
                budgetMinInput.placeholder = `Multi-country min: $${budgetMinInput.value.toLocaleString()}`;
                budgetMaxInput.placeholder = `Multi-country max: $${budgetMaxInput.value.toLocaleString()}`;
            }
        }
    }
}

// Toggle all countries selection
function toggleAllCountries() {
    const checkboxes = document.querySelectorAll('input[name="preferred_countries"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
    });
    
    updateBudgetHint();
}
