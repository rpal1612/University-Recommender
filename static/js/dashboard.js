// Dashboard JavaScript
let userData = null;
let currentTab = 'stats';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

// Switch between tabs
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');

    currentTab = tabName;

    // Load data based on tab
    if (tabName === 'history' && !document.querySelector('#historyContainer .history-item')) {
        loadHistory();
    } else if (tabName === 'wishlist') {
        loadWishlist();
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        // Check authentication
        const authResponse = await fetch('/api/check-auth');
        const authData = await authResponse.json();

        if (!authData.authenticated) {
            window.location.href = '/login';
            return;
        }

        // Load user data
        const userResponse = await fetch('/api/user');
        if (!userResponse.ok) {
            throw new Error('Failed to load user data');
        }

        userData = await userResponse.json();
        displayUserInfo(userData);

        // Load search history initially
        await loadHistory();

    } catch (error) {
        console.error('Dashboard error:', error);
        document.getElementById('historyContainer').innerHTML = `
            <div class="empty-state">
                <h4>Error loading dashboard</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Display user information and statistics
function displayUserInfo(data) {
    const user = data.user;
    const stats = data.stats || {};

    document.getElementById('userName').textContent = user.name;
    document.getElementById('userNameWelcome').textContent = user.name.split(' ')[0];
    
    document.getElementById('totalSearches').textContent = stats.total_searches || 0;
    document.getElementById('uniqueUniversities').textContent = stats.unique_universities || 0;
    document.getElementById('wishlistCount').textContent = stats.wishlist_count || 0;

    if (user.memberSince) {
        const memberDate = new Date(user.memberSince);
        const today = new Date();
        const daysDiff = Math.floor((today - memberDate) / (1000 * 60 * 60 * 24));
        document.getElementById('memberDays').textContent = daysDiff;
    }
}

// Load search history
async function loadHistory() {
    try {
        const historyResponse = await fetch('/api/history');
        if (historyResponse.ok) {
            const historyData = await historyResponse.json();
            displayHistory(historyData.history);
        } else {
            displayHistory([]);
        }
    } catch (error) {
        console.error('Error loading history:', error);
        displayHistory([]);
    }
}

// Display search history
function displayHistory(history) {
    const container = document.getElementById('historyContainer');

    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <h4>No search history yet</h4>
                <p>Your university searches will appear here</p>
            </div>
        `;
        return;
    }

    let html = '';
    history.forEach((entry, index) => {
        const date = new Date(entry.timestamp);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        html += `
            <div class="history-item" onclick="showSearchDetails(${index})">
                <div class="history-header">
                    <h4><i class="fas fa-search"></i> Search on ${formattedDate}</h4>
                    <i class="fas fa-chevron-right"></i>
                </div>
                <p><strong>Results:</strong> ${entry.recommendations ? entry.recommendations.length : 0} universities</p>
                <p class="click-hint"><i class="fas fa-info-circle"></i> Click to view full details</p>
            </div>
        `;
    });

    container.innerHTML = html;
    
    // Store history data for modal access
    window.searchHistoryData = history;
}

// Show search details in modal
function showSearchDetails(index) {
    const entry = window.searchHistoryData[index];
    if (!entry) return;
    
    const date = new Date(entry.timestamp);
    const formattedDate = date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Build preferences display
    let preferencesHTML = '';
    if (entry.preferences) {
        const prefs = entry.preferences;
        preferencesHTML = `
            <div class="detail-section">
                <h4><i class="fas fa-sliders-h"></i> Search Preferences</h4>
                <div class="detail-grid">
                    ${prefs.greV ? `<div class="detail-item"><strong>GRE Verbal:</strong> ${prefs.greV}</div>` : ''}
                    ${prefs.greQ ? `<div class="detail-item"><strong>GRE Quantitative:</strong> ${prefs.greQ}</div>` : ''}
                    ${prefs.greA ? `<div class="detail-item"><strong>GRE Analytical:</strong> ${prefs.greA}</div>` : ''}
                    ${prefs.cgpa ? `<div class="detail-item"><strong>GPA:</strong> ${prefs.cgpa}</div>` : ''}
                    ${prefs.ielts ? `<div class="detail-item"><strong>IELTS:</strong> ${prefs.ielts}</div>` : ''}
                    ${prefs.toefl ? `<div class="detail-item"><strong>TOEFL:</strong> ${prefs.toefl}</div>` : ''}
                    ${prefs.major ? `<div class="detail-item"><strong>Major:</strong> ${prefs.major}</div>` : ''}
                    ${prefs.workExperience ? `<div class="detail-item"><strong>Work Experience:</strong> ${prefs.workExperience} years</div>` : ''}
                    ${prefs.publications ? `<div class="detail-item"><strong>Publications:</strong> ${prefs.publications}</div>` : ''}
                    ${prefs.countries ? `<div class="detail-item full-width"><strong>Countries:</strong> ${Array.isArray(prefs.countries) ? prefs.countries.join(', ') : prefs.countries}</div>` : ''}
                    ${prefs.budget ? `<div class="detail-item"><strong>Budget:</strong> $${prefs.budget}</div>` : ''}
                    ${prefs.universityType ? `<div class="detail-item"><strong>University Type:</strong> ${prefs.universityType}</div>` : ''}
                    ${prefs.duration ? `<div class="detail-item"><strong>Duration:</strong> ${prefs.duration}</div>` : ''}
                    ${prefs.researchFocused !== undefined ? `<div class="detail-item"><strong>Research Focused:</strong> ${prefs.researchFocused ? 'Yes' : 'No'}</div>` : ''}
                    ${prefs.internshipOpportunities !== undefined ? `<div class="detail-item"><strong>Internship Opportunities:</strong> ${prefs.internshipOpportunities ? 'Yes' : 'No'}</div>` : ''}
                    ${prefs.postStudyWorkVisa !== undefined ? `<div class="detail-item"><strong>Post-Study Work Visa:</strong> ${prefs.postStudyWorkVisa ? 'Yes' : 'No'}</div>` : ''}
                </div>
            </div>
        `;
    }
    
    // Build recommendations display
    let recommendationsHTML = '';
    if (entry.recommendations && entry.recommendations.length > 0) {
        recommendationsHTML = `
            <div class="detail-section">
                <h4><i class="fas fa-university"></i> Recommended Universities (${entry.recommendations.length})</h4>
                <div class="recommendations-list">
                    ${entry.recommendations.map((uni, idx) => `
                        <div class="recommendation-card">
                            <div class="recommendation-header">
                                <span class="recommendation-rank">#${idx + 1}</span>
                                <h5>${uni.university_name || uni.name || 'Unknown University'}</h5>
                            </div>
                            <div class="recommendation-details">
                                ${uni.country ? `<span><i class="fas fa-globe"></i> ${uni.country}</span>` : ''}
                                ${uni.ranking && uni.ranking !== 999 ? `<span><i class="fas fa-trophy"></i> Rank #${uni.ranking}</span>` : ''}
                                ${uni.match_score ? `<span class="match-score"><i class="fas fa-star"></i> ${(uni.match_score * 100).toFixed(1)}% Match</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Create and show modal
    const modalHTML = `
        <div class="modal-overlay" onclick="closeSearchModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3><i class="fas fa-search"></i> Search Details</h3>
                    <button class="modal-close" onclick="closeSearchModal()">✕</button>
                </div>
                <div class="modal-body">
                    <div class="search-date">
                        <i class="fas fa-calendar"></i> ${formattedDate}
                    </div>
                    ${preferencesHTML}
                    ${recommendationsHTML}
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    const existingModal = document.getElementById('searchModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modalDiv = document.createElement('div');
    modalDiv.id = 'searchModal';
    modalDiv.innerHTML = modalHTML;
    document.body.appendChild(modalDiv);
}

// Close search modal
function closeSearchModal() {
    const modal = document.getElementById('searchModal');
    if (modal) {
        modal.remove();
    }
}

// Load wishlist
async function loadWishlist() {
    const container = document.getElementById('wishlistContainer');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading wishlist...</p></div>';

    try {
        const response = await fetch('/api/wishlist');
        if (response.ok) {
            const data = await response.json();
            displayWishlist(data.wishlist);
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h4>Error loading wishlist</h4></div>';
        }
    } catch (error) {
        console.error('Error loading wishlist:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h4>Error loading wishlist</h4></div>';
    }
}

// Display wishlist
function displayWishlist(wishlist) {
    const container = document.getElementById('wishlistContainer');

    if (!wishlist || wishlist.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-heart"></i>
                <h4>Your wishlist is empty</h4>
                <p>Start adding universities you're interested in from the recommendations page</p>
                <a href="/graduate" class="nav-btn" style="margin-top: 20px; display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px;">
                    <i class="fas fa-search"></i> Find Universities
                </a>
            </div>
        `;
        return;
    }

    let html = '<div class="wishlist-grid">';
    wishlist.forEach(item => {
        const addedDate = new Date(item.added_at).toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric'
        });

        html += `
            <div class="wishlist-card">
                <div class="wishlist-header">
                    <h4>${item.university_name}</h4>
                    <button class="remove-btn" onclick="removeFromWishlist('${item.university_name.replace(/'/g, "\\'")}')">
                        ✕
                    </button>
                </div>
                
                ${item.match_score ? `
                    <div class="match-badge-wishlist">
                        <i class="fas fa-star"></i>
                        ${(item.match_score * 100).toFixed(1)}% Match
                    </div>
                ` : ''}
                
                <div class="wishlist-info">
                    ${item.country ? `
                        <div class="wishlist-info-item">
                            <i class="fas fa-globe"></i>
                            <strong>Country:</strong> ${item.country}
                        </div>
                    ` : ''}
                    
                    ${item.ranking && item.ranking !== 999 ? `
                        <div class="wishlist-info-item">
                            <i class="fas fa-trophy"></i>
                            <strong>Rank:</strong> #${item.ranking}
                        </div>
                    ` : ''}
                    
                    ${item.tuition ? `
                        <div class="wishlist-info-item">
                            <i class="fas fa-dollar-sign"></i>
                            <strong>Tuition:</strong> $${item.tuition.toLocaleString()}/year
                        </div>
                    ` : ''}
                </div>
                
                <p class="added-date">
                    <i class="fas fa-calendar-plus"></i>
                    Added on ${addedDate}
                </p>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

// Remove from wishlist
async function removeFromWishlist(universityName) {
    if (!confirm(`Remove ${universityName} from wishlist?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/wishlist/${encodeURIComponent(universityName)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Reload wishlist
            loadWishlist();
            
            // Update stats
            const currentCount = parseInt(document.getElementById('wishlistCount').textContent);
            document.getElementById('wishlistCount').textContent = Math.max(0, currentCount - 1);
            
            // Show success message
            showNotification('Removed from wishlist successfully!', 'success');
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to remove from wishlist', 'error');
        }
    } catch (error) {
        console.error('Error removing from wishlist:', error);
        showNotification('Failed to remove from wishlist', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Logout function
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });

        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('Failed to logout. Please try again.');
    }
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
