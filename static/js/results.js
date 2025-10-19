// University Recommender - Results JavaScript
// Created: October 19, 2025

let allUniversities = [];
let filteredUniversities = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Universities data will be injected by the server
    if (typeof universitiesData !== 'undefined') {
        allUniversities = universitiesData;
        filteredUniversities = [...allUniversities];
    }
    
    populateCountryFilter();
    applyFilters();
});

// Populate country filter dropdown
function populateCountryFilter() {
    const countries = [...new Set(allUniversities.map(u => u.country))].sort();
    const select = document.getElementById('filterCountry');
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

// Apply filters and sorting
function applyFilters() {
    const sortBy = document.getElementById('sortBy').value;
    const filterCountry = document.getElementById('filterCountry').value;
    const filterType = document.getElementById('filterType').value;
    const filterBudget = parseInt(document.getElementById('filterBudget').value);
    
    // Filter
    filteredUniversities = allUniversities.filter(uni => {
        if (filterCountry && uni.country !== filterCountry) return false;
        if (filterType && uni.type !== filterType) return false;
        if (filterBudget < 999999 && uni.tuition_value > filterBudget) return false;
        return true;
    });
    
    // Sort
    filteredUniversities.sort((a, b) => {
        switch(sortBy) {
            case 'score':
                return (b.score || 0) - (a.score || 0);
            case 'fees-low':
                return (a.tuition_value || 999999) - (b.tuition_value || 999999);
            case 'fees-high':
                return (b.tuition_value || 0) - (a.tuition_value || 0);
            case 'country':
                return a.country.localeCompare(b.country);
            default:
                return (b.score || 0) - (a.score || 0);
        }
    });
    
    displayUniversities();
}

// Reset all filters
function resetFilters() {
    document.getElementById('sortBy').value = 'score';
    document.getElementById('filterCountry').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterBudget').value = '999999';
    applyFilters();
}

// Display universities in grid format
function displayUniversities() {
    const container = document.getElementById('universitiesList');
    document.getElementById('resultsCount').textContent = filteredUniversities.length;
    
    if (filteredUniversities.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No Matches Found</h3>
                <p>Try adjusting your filters to see more universities</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = filteredUniversities.map((uni, index) => `
        <div class="university-card">
            <div class="card-header">
                <div class="university-name">
                    <i class="fas fa-university"></i>
                    <h3>${uni.name}</h3>
                    <a href="${uni.website || 'https://www.google.com/search?q=' + encodeURIComponent(uni.name + ' university official website') + '&btnI=1'}" 
                       target="_blank" 
                       class="website-link" 
                       title="Visit Website">
                        <i class="fab fa-google"></i>
                    </a>
                </div>
                <div class="match-badge">
                    ${(uni.score * 100).toFixed(1)}% Match
                </div>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <i class="fas fa-globe"></i>
                    <strong>Country:</strong> <span>${uni.country}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-trophy"></i>
                    <strong>Rank:</strong> <span>#${uni.ranking === 999 ? 'N/A' : uni.ranking}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-dollar-sign"></i>
                    <strong>Tuition:</strong> <span>${uni.tuition}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-building"></i>
                    <strong>Type:</strong> <span>${uni.type}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-clock"></i>
                    <strong>Duration:</strong> <span>${uni.duration}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-language"></i>
                    <strong>IELTS:</strong> <span>${uni.ielts} | </span><strong>TOEFL:</strong> <span>${uni.toefl}</span>
                </div>
            </div>
            
            <div class="feature-tags">
                ${uni.research_focused ? '<div class="feature-tag"><i class="fas fa-microscope"></i> Research-Focused</div>' : ''}
                ${uni.internship_opportunities ? '<div class="feature-tag"><i class="fas fa-briefcase"></i> Internships</div>' : ''}
                ${uni.post_study_work_visa ? '<div class="feature-tag"><i class="fas fa-passport"></i> Work Visa</div>' : ''}
            </div>
        </div>
    `).join('');
}
