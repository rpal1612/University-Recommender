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
    if (tabName === 'wishlist') {
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

    } catch (error) {
        console.error('Dashboard error:', error);
        alert('Error loading dashboard: ' + error.message);
    }
}

    // Display user information and statistics
function displayUserInfo(data) {
    const user = data.user;
    const stats = data.stats || {};

    console.log('=== DASHBOARD DEBUG ===');
    console.log('Full data received:', data);
    console.log('Stats object:', stats);
    console.log('Top countries:', stats.top_countries);
    console.log('Best matches:', stats.best_matches);
    console.log('Category distribution:', stats.category_distribution);
    console.log('=====================');

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

    // Add insights section
    console.log('Adding dashboard insights with data:', data);
    addDashboardInsights(data);
}

// Add dashboard insights with charts
function addDashboardInsights(data) {
    const statsGrid = document.getElementById('statsGrid');
    
    // Add insights section after stats grid (only Top Countries chart)
    const insightsSection = document.createElement('div');
    insightsSection.className = 'insights-section';
    insightsSection.innerHTML = `
        <h3><i class="fas fa-lightbulb"></i> Your Insights</h3>
        <div class="insights-grid">
            <div class="insight-card" style="grid-column: span 2;">
                <h4><i class="fas fa-chart-line"></i> Top Countries You've Explored</h4>
                <canvas id="countriesChart"></canvas>
            </div>
        </div>
    `;
    
    if (!document.querySelector('.insights-section')) {
        statsGrid.parentNode.insertBefore(insightsSection, statsGrid.nextSibling);
        
        // Load charts after a short delay
        setTimeout(() => {
            loadDashboardCharts(data);
        }, 100);
    }
}

// Load dashboard charts
function loadDashboardCharts(data) {
    const stats = data.stats || {};
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }
    
    // Countries chart
    if (stats.top_countries && stats.top_countries.length > 0 && document.getElementById('countriesChart')) {
        try {
            const ctx = document.getElementById('countriesChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: stats.top_countries.map(c => c.country),
                    datasets: [{
                        data: stats.top_countries.map(c => c.count),
                        backgroundColor: ['#667eea', '#4caf50', '#ff9800', '#2196f3', '#f44336']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating countries chart:', error);
            document.getElementById('countriesChart').parentElement.innerHTML = '<p style="text-align: center; color: #666;">Perform searches to see country distribution</p>';
        }
    } else if (document.getElementById('countriesChart')) {
        document.getElementById('countriesChart').parentElement.innerHTML = '<p style="text-align: center; color: #666; padding: 40px 20px;">Perform searches to see country distribution</p>';
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
