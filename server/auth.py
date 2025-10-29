"""
Authentication routes and user management
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
import re

auth_bp = Blueprint('auth', __name__)

# Will be set by main app
db = None

def init_auth(database):
    """Initialize auth blueprint with database"""
    global db
    db = database

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login_page'))
        
        if session.get('user_role') != 'admin':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

# ==================== PAGE ROUTES ====================

@auth_bp.route('/login')
def login_page():
    """Render login page"""
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect('/admin')
        return redirect('/dashboard')
    return render_template('login.html')

@auth_bp.route('/signup')
def signup_page():
    """Render signup page"""
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect('/admin')
        return redirect('/dashboard')
    return render_template('signup.html')

# ==================== API ROUTES ====================

@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    """Handle user registration"""
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        full_name = data.get('fullName', '').strip()
        
        # Validation checks
        if not email or not password or not full_name:
            return jsonify({'error': 'All fields are required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({'error': msg}), 400
        
        if len(full_name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters'}), 400
        
        # Check if email already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        user_id = db.create_user(email, password, full_name)
        
        # Auto-login after signup
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = full_name
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'redirect': '/dashboard'
        }), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Verify credentials
        user = db.verify_user(email, password)
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Set session
        session['user_id'] = str(user['_id'])
        session['user_email'] = user['email']
        session['user_name'] = user['full_name']
        session['user_role'] = user.get('role', 'user')
        session.permanent = remember
        
        # Redirect based on role
        redirect_url = '/admin' if user.get('role') == 'admin' else '/dashboard'
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'name': user['full_name'],
                'email': user['email'],
                'role': user.get('role', 'user')
            },
            'redirect': redirect_url
        }), 200
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully',
        'redirect': '/login'
    }), 200

@auth_bp.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        user = db.get_user_by_id(session['user_id'])
        
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        # Get user stats
        stats = db.get_user_stats(session['user_id'])
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['full_name'],
                'memberSince': user['created_at'].isoformat() if user.get('created_at') else None,
                'lastLogin': user['last_login'].isoformat() if user.get('last_login') else None,
                'totalSearches': user.get('total_searches', 0)
            },
            'stats': stats
        }), 200
    
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to fetch user data'}), 500

@auth_bp.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')
        confirm_password = data.get('confirmPassword', '')
        
        # Validate input
        if not current_password or not new_password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': msg}), 400
        
        # Verify current password
        user = db.verify_user(session['user_email'], current_password)
        if not user:
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        import bcrypt
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        success = db.update_user(session['user_id'], {
            'password_hash': password_hash
        })
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to update password'}), 500
    
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/api/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        # Verify password
        user = db.verify_user(session['user_email'], password)
        if not user:
            return jsonify({'error': 'Incorrect password'}), 401
        
        # Delete user data (searches, recommendations, user)
        user_id = session['user_id']
        
        # Delete search history
        db.search_history.delete_many({'user_id': user_id})
        
        # Delete recommendations
        db.recommendations.delete_many({'user_id': user_id})
        
        # Delete user
        from bson.objectid import ObjectId
        db.users.delete_one({'_id': ObjectId(user_id)})
        
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully',
            'redirect': '/signup'
        }), 200
    
    except Exception as e:
        print(f"Delete account error: {e}")
        return jsonify({'error': 'Account deletion failed'}), 500

@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'email': session.get('user_email'),
                'name': session.get('user_name')
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200
