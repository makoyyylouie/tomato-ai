# =============================================================================
# auth.py
# Authentication Module for Tomato Ripeness & Disease Checker
# =============================================================================

import streamlit as st
import json
import os
import hashlib
from datetime import datetime


# File to store user credentials
USERS_FILE = "users_db.json"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def validate_email(email):
    """Basic email validation"""
    return "@" in email and "." in email.split("@")[1]

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, "Password is valid"

# =============================================================================
# AUTHENTICATION UI FUNCTIONS
# =============================================================================

def login_user(username, password):
    """Authenticate user login"""
    users = load_users()
    
    if username in users:
        if users[username]['password'] == hash_password(password):
            # Update last login
            users[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_users(users)
            return True, users[username]
    return False, None

def register_user(username, email, password, full_name):
    """Register a new user"""
    users = load_users()
    
    # Check if username already exists
    if username in users:
        return False, "Username already exists"
    
    # Validate email
    if not validate_email(email):
        return False, "Invalid email format"
    
    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return False, message
    
    # Create new user
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'full_name': full_name,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_login': None
    }
    
    save_users(users)
    return True, "Registration successful!"

# =============================================================================
# MAIN AUTHENTICATION UI
# =============================================================================

def show_login_page():
    """Display login/signup page and handle authentication"""
    
    # Custom CSS for login page
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        .login-header {
            text-align: center;
            color: #2E7D32;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .login-subtitle {
            text-align: center;
            color: #757575;
            margin-bottom: 30px;
        }
        .auth-tabs {
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-header">🍅 Tomato AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Ripeness & Disease Detection System</div>', unsafe_allow_html=True)
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    # =============================================================================
    # LOGIN TAB
    # =============================================================================
    with tab1:
        st.markdown("### Welcome Back!")
        
        with st.form("login_form"):
            login_username = st.text_input("Username", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_login = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit_login:
                if not login_username or not login_password:
                    st.error("❌ Please fill in all fields")
                else:
                    success, user_data = login_user(login_username, login_password)
                    
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = login_username
                        st.session_state['user_data'] = user_data
                        st.success(f"✅ Welcome back, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
    
    # =============================================================================
    # SIGN UP TAB
    # =============================================================================
    with tab2:
        st.markdown("### Create New Account")
        
        with st.form("signup_form"):
            signup_fullname = st.text_input("Full Name", placeholder="Enter your full name")
            signup_email = st.text_input("Email", placeholder="Enter your email")
            signup_username = st.text_input("Username", placeholder="Choose a username")
            signup_password = st.text_input("Password", type="password", placeholder="Create a password (min. 6 characters)")
            signup_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_signup = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
            
            if submit_signup:
                if not all([signup_fullname, signup_email, signup_username, signup_password, signup_confirm_password]):
                    st.error("❌ Please fill in all fields")
                elif signup_password != signup_confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    success, message = register_user(signup_username, signup_email, signup_password, signup_fullname)
                    
                    if success:
                        st.success(f"✅ {message} Please login to continue.")
                    else:
                        st.error(f"❌ {message}")
    
    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #9E9E9E; font-size: 12px;'>Secure Authentication System | Tomato AI</p>", unsafe_allow_html=True)

def show_logout_button():
    """Displays the profile and logout buttons in the Sidebar"""
    if st.session_state.get('logged_in', False):
        # This tells Streamlit to put everything below inside the sidebar
        with st.sidebar:
            st.markdown("### 🍅 Hello, ToMatetoes!")
            
            # Profile Button
            if st.button("👤 View Profile", key="view_profile_btn", use_container_width=True):
                st.session_state.show_profile = not st.session_state.get('show_profile', False)
                st.rerun()  # Add this to refresh and show profile
            
            # Show profile info if toggled
            show_profile_page()
            
            # Logout Button (Red Button)
            if st.button("🚪 Logout", key="logout_btn", type="primary", use_container_width=True):
                # Clear user session data but keep history file intact
                keys_to_clear = ['logged_in', 'username', 'user_data', 'show_profile', 'show_recent']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Reset history loaded flag so next login reloads fresh data
                st.rerun()
            
            st.markdown("---") # Adds a divider line

def show_profile_page():
    """Display user profile information in the sidebar"""
    if st.session_state.get('show_profile', False) and st.session_state.get('logged_in', False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Profile")
            
            user_data = st.session_state.get('user_data', {})
            
            # Create a nice profile card
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #2E7D32;">{user_data.get('full_name', 'Unknown')}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 14px;">@{st.session_state.get('username', 'unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Profile details
            st.markdown("**📧 Email:**")
            st.write(user_data.get('email', 'Not provided'))
            
            st.markdown("**📅 Member Since:**")
            st.write(user_data.get('created_at', 'Unknown'))
            
            st.markdown("**🕐 Last Login:**")
            last_login = user_data.get('last_login')
            st.write(last_login if last_login else 'First time login')
            
            if st.button("✖ Close Profile", key="close_profile_btn", use_container_width=True):
                st.session_state.show_profile = False
                st.rerun()
            
            st.markdown("---")



def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """Get current logged in user information"""
    if check_authentication():
        return {
            'username': st.session_state.get('username'),
            'user_data': st.session_state.get('user_data')
        }
    return None