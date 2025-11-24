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
    const filterCategory = document.getElementById('filterCategory') ? document.getElementById('filterCategory').value : '';
    
    // Filter
    filteredUniversities = allUniversities.filter(uni => {
        if (filterCountry && uni.country !== filterCountry) return false;
        if (filterType && uni.type !== filterType) return false;
        if (filterBudget < 999999 && uni.tuition_value > filterBudget) return false;
        if (filterCategory && uni.category !== filterCategory) return false;
        return true;
    });
    
    // Sort
    filteredUniversities.sort((a, b) => {
        switch(sortBy) {
            case 'score':
                return (b.score || 0) - (a.score || 0);
            case 'admission':
                return (b.admission_probability || 0) - (a.admission_probability || 0);
            case 'fees-low':
                return (a.tuition_value || 999999) - (b.tuition_value || 999999);
            case 'fees-high':
                return (b.tuition_value || 0) - (a.tuition_value || 0);
            case 'country':
                return a.country.localeCompare(b.country);
            case 'ranking':
                return (a.ranking || 999) - (b.ranking || 999);
            default:
                return (b.score || 0) - (a.score || 0);
        }
    });
    
    displayUniversities();
    updateCategoryStats();
}

// Reset all filters
function resetFilters() {
    document.getElementById('sortBy').value = 'score';
    document.getElementById('filterCountry').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterBudget').value = '999999';
    if (document.getElementById('filterCategory')) {
        document.getElementById('filterCategory').value = '';
    }
    applyFilters();
}

// Update category statistics
function updateCategoryStats() {
    const categories = {
        'Safety': 0,
        'Target': 0,
        'Reach': 0,
        'Long Shot': 0
    };
    
    filteredUniversities.forEach(uni => {
        if (uni.category && categories.hasOwnProperty(uni.category)) {
            categories[uni.category]++;
        }
    });
    
    // Update stats display if elements exist
    if (document.getElementById('safetyCount')) {
        document.getElementById('safetyCount').textContent = categories['Safety'];
        document.getElementById('targetCount').textContent = categories['Target'];
        document.getElementById('reachCount').textContent = categories['Reach'];
        document.getElementById('longShotCount').textContent = categories['Long Shot'];
    }
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
    
    container.innerHTML = filteredUniversities.map((uni, index) => {
        // Determine category badge styling
        const categoryColors = {
            'Safety': '#4caf50',
            'Target': '#2196f3',
            'Reach': '#ff9800',
            'Long Shot': '#f44336'
        };
        const categoryColor = categoryColors[uni.category] || '#667eea';
        
        return `
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
                <div class="match-badges">
                    <div class="match-badge">
                        ${(uni.score * 100).toFixed(1)}% Match
                    </div>
                    <div class="category-badge" style="background: ${categoryColor};">
                        ${uni.category || 'N/A'}
                    </div>
                </div>
            </div>
            
            <div class="admission-probability-bar">
                <div class="probability-label">
                    <i class="fas fa-chart-line"></i> Admission Probability: 
                    <strong>${uni.admission_probability || 0}%</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${uni.admission_probability || 0}%; background: ${categoryColor};"></div>
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
            
            ${uni.explanation ? `
            <div class="explanation-section">
                <button class="explanation-toggle" onclick="toggleExplanation(${index})">
                    <i class="fas fa-lightbulb"></i> Why this university?
                    <i class="fas fa-chevron-down toggle-icon"></i>
                </button>
                <div class="explanation-content" id="explanation-${index}">
                    ${uni.explanation.key_strengths ? `
                    <div class="explanation-item">
                        <h4><i class="fas fa-star"></i> Key Strengths</h4>
                        <ul>
                            ${uni.explanation.key_strengths.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                    ${uni.explanation.considerations ? `
                    <div class="explanation-item">
                        <h4><i class="fas fa-exclamation-circle"></i> Considerations</h4>
                        <ul>
                            ${uni.explanation.considerations.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                    ${uni.explanation.admission_insight ? `
                    <div class="explanation-item">
                        <h4><i class="fas fa-chart-line"></i> Admission Insight</h4>
                        <p>${uni.explanation.admission_insight.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>
                    </div>
                    ` : ''}
                    ${uni.explanation.financial_insight ? `
                    <div class="explanation-item">
                        <h4><i class="fas fa-money-bill-wave"></i> Financial Insight</h4>
                        <p>${uni.explanation.financial_insight}</p>
                    </div>
                    ` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="card-actions">
                <button class="wishlist-btn" onclick='addToWishlist(${index}, event)'>
                    <i class="fas fa-heart"></i> Add to Wishlist
                </button>
            </div>
        </div>
        `;
    }).join('');
}

// Add university to wishlist
async function addToWishlist(universityIndex, event) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    
    // Get university data from filtered list (without explanation to avoid JSON issues)
    const uni = filteredUniversities[universityIndex];
    const universityData = {
        name: uni.name,
        country: uni.country,
        ranking: uni.ranking,
        tuition: uni.tuition,
        tuition_value: uni.tuition_value,
        type: uni.type,
        duration: uni.duration,
        ielts: uni.ielts,
        toefl: uni.toefl,
        score: uni.score,
        admission_probability: uni.admission_probability,
        category: uni.category,
        research_focused: uni.research_focused,
        internship_opportunities: uni.internship_opportunities,
        post_study_work_visa: uni.post_study_work_visa
    };
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    
    try {
        const response = await fetch('/api/wishlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(universityData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            btn.innerHTML = '<i class="fas fa-check"></i> Added!';
            btn.style.background = '#4caf50';
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-heart"></i> In Wishlist';
                btn.style.background = '#667eea';
            }, 2000);
        } else {
            alert(data.message || data.error || 'Failed to add to wishlist');
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Error adding to wishlist:', error);
        alert('Failed to add to wishlist. Please try again.');
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Toggle explanation section
function toggleExplanation(index) {
    const content = document.getElementById(`explanation-${index}`);
    const isOpen = content.classList.contains('open');
    
    // Close all other explanations
    document.querySelectorAll('.explanation-content').forEach(el => {
        el.classList.remove('open');
    });
    document.querySelectorAll('.explanation-toggle').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Toggle current explanation
    if (!isOpen) {
        content.classList.add('open');
        event.target.closest('.explanation-toggle').classList.add('active');
    }
}

// Export results to PDF
async function exportToPDF() {
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
    btn.disabled = true;

    try {
        // Create a simplified version of results for PDF
        const pdfContent = {
            total: filteredUniversities.length,
            generatedAt: new Date().toLocaleString(),
            universities: filteredUniversities.slice(0, 20).map(uni => ({
                name: uni.name,
                country: uni.country,
                score: (uni.score * 100).toFixed(1),
                admission_probability: uni.admission_probability,
                category: uni.category,
                ranking: uni.ranking,
                tuition: uni.tuition,
                type: uni.type
            }))
        };

        // Send to backend for PDF generation
        const response = await fetch('/api/export-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pdfContent)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `university-recommendations-${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            throw new Error('PDF generation failed');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export PDF. Please try again.');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Show score comparison chart
function showScoreChart() {
    const modal = document.createElement('div');
    modal.className = 'chart-modal';
    modal.innerHTML = `
        <div class="chart-modal-content">
            <div class="chart-header">
                <h3><i class="fas fa-chart-bar"></i> Score Breakdown Comparison</h3>
                <button onclick="this.closest('.chart-modal').remove()" class="close-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="chart-container">
                <canvas id="scoreChart"></canvas>
            </div>
            <div class="chart-footer" style="text-align: center; padding: 10px; color: #666; font-size: 12px;">
                Comparing top 5 universities across 5 scoring dimensions
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // Create chart using Chart.js (loaded via CDN)
    const ctx = document.getElementById('scoreChart').getContext('2d');
    const topUniversities = filteredUniversities.slice(0, 5); // Show top 5 for better visibility
    
    // Color palette for different universities
    const colors = [
        { bg: 'rgba(102, 126, 234, 0.2)', border: '#667eea' },
        { bg: 'rgba(76, 175, 80, 0.2)', border: '#4caf50' },
        { bg: 'rgba(255, 152, 0, 0.2)', border: '#ff9800' },
        { bg: 'rgba(33, 150, 243, 0.2)', border: '#2196f3' },
        { bg: 'rgba(244, 67, 54, 0.2)', border: '#f44336' }
    ];
    
    // Create datasets for each university showing their 5 score dimensions
    const datasets = topUniversities.map((uni, idx) => {
        // Extract breakdown scores or use defaults
        const breakdown = uni.breakdown || {};
        const academic = breakdown.academic_fit?.score || (uni.score * 100 * 0.3);
        const admission = breakdown.admission_probability?.score || (uni.score * 100 * 0.25);
        const financial = breakdown.financial_fit?.score || (uni.score * 100 * 0.2);
        const career = breakdown.career_outcomes?.score || (uni.score * 100 * 0.15);
        const personal = breakdown.personal_fit?.score || (uni.score * 100 * 0.1);
        
        return {
            label: uni.name.length > 25 ? uni.name.substring(0, 25) + '...' : uni.name,
            data: [academic, admission, financial, career, personal],
            backgroundColor: colors[idx].bg,
            borderColor: colors[idx].border,
            borderWidth: 2,
            pointBackgroundColor: colors[idx].border,
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: colors[idx].border
        };
    });
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Academic Fit', 'Admission Probability', 'Financial Fit', 'Career Outcomes', 'Personal Fit'],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.r.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}
