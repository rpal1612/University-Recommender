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
        
        countries.forEach(country => {
            const div = document.createElement('div');
            div.className = 'country-checkbox-item';
            div.innerHTML = `
                <input type="checkbox" name="preferred_countries" value="${country}" id="country_${country}">
                <label for="country_${country}">${country}</label>
            `;
            container.appendChild(div);
        });
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

// Toggle all countries checkbox
function toggleAllCountries() {
    const checkboxes = document.querySelectorAll('#countryCheckboxes input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => cb.checked = !allChecked);
}

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
