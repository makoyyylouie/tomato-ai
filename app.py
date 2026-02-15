# =============================================================================
# app.py
# TOMATO RIPENESS & DISEASE CHECKER - Streamlit Web Application (WITH AUTH)
# =============================================================================
# how run this in terminal/powershell 1st: cd "C:\Users\David\OneDrive\Documents\Tomato AI Final" 2nd: streamlit run app.py
import streamlit as st
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import json
import os
import auth

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Tomato Ripeness & Disease Checker",
    page_icon="🍅",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =============================================================================
# SESSION STATE INITIALIZATION (FIXED - Added camera_mode)
# =============================================================================
if 'recent_scans' not in st.session_state:
    st.session_state.recent_scans = []
if 'show_recent' not in st.session_state:
    st.session_state.show_recent = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'history_loaded' not in st.session_state:
    st.session_state.history_loaded = False
if 'camera_mode' not in st.session_state:
    st.session_state.camera_mode = "environment"  # Default to back camera

# =============================================================================
# HELPER FUNCTIONS (Define these early so they can be used anywhere)
# =============================================================================

def load_user_history():
    """Load scan history for current user from JSON file"""
    history_file = "scan_history.json"
    username = st.session_state.get('username', 'Guest')
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            # Filter for current user only
            user_scans = [s for s in history if s.get('username') == username]
            return user_scans
        except:
            return []
    return []

def delete_scan(scan_id):
    """Delete a specific scan from history"""
    history_file = "scan_history.json"
    username = st.session_state.get('username', 'Guest')
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Find and remove the scan
            scan_to_delete = None
            for scan in history:
                if scan.get('scan_id') == scan_id and scan.get('username') == username:
                    scan_to_delete = scan
                    break
            
            if scan_to_delete:
                # Delete associated image if it exists
                img_path = scan_to_delete.get('image_path')
                if img_path and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass
                
                # Remove from history
                history.remove(scan_to_delete)
                
                # Save updated history
                with open(history_file, 'w') as f:
                    json.dump(history, f, indent=4)
                
                # Update session state
                st.session_state.recent_scans = [s for s in history if s.get('username') == username]
                return True
        except Exception as e:
            st.error(f"Error deleting scan: {e}")
            return False
    return False

def save_scan_to_history(mode, status, ripeness, diseases, image_file=None):
    """Saves scan data to a JSON file so it persists after Logout"""
    history_file = "scan_history.json"
    username = st.session_state.get('username', 'Guest')
    
    # Create scans directory if it doesn't exist
    scans_dir = "user_scans"
    if not os.path.exists(scans_dir):
        os.makedirs(scans_dir)
    
    # Save image if provided
    image_path = None
    if image_file is not None:
        try:
            # Reset file pointer to beginning
            image_file.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{username}_{timestamp}.jpg"
            image_path = os.path.join(scans_dir, image_filename)
            
            # Save image to disk
            with open(image_path, "wb") as f:
                f.write(image_file.getvalue())
        except Exception as e:
            st.error(f"Error saving image: {e}")
            image_path = None
    
    # Create the data entry
    new_scan = {
        "username": username,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "status": status,
        "ripeness": ripeness if ripeness else "N/A",
        "diseases": [d['name'].replace('-', ' ').title() for d in diseases] if diseases else [],
        "image_path": image_path,
        "scan_id": f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    }
    
    # Load existing history from file
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Add new scan to the top (limit to last 100 scans per user)
    history.insert(0, new_scan)
    
    # Keep only last 100 scans per user to prevent file from getting too large
    user_scans = [s for s in history if s.get('username') == username]
    other_scans = [s for s in history if s.get('username') != username]
    
    if len(user_scans) > 100:
        # Remove old scans and their images
        for old_scan in user_scans[100:]:
            if old_scan.get('image_path') and os.path.exists(old_scan['image_path']):
                try:
                    os.remove(old_scan['image_path'])
                except:
                    pass
        user_scans = user_scans[:100]
    
    # Combine back
    history = user_scans + other_scans
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)
    
    # Update current session view
    st.session_state.recent_scans = user_scans

# =============================================================================
# AUTHENTICATION CHECK
# =============================================================================
if not auth.check_authentication():
    # Show login page if not authenticated
    auth.show_login_page()
    st.stop()  # Stop execution here until user logs in

# =============================================================================
# USER IS AUTHENTICATED - SHOW MAIN APP
# =============================================================================

# Show logout button in sidebar
auth.show_logout_button()

# =============================================================================
# DISEASE INFORMATION DATABASE
# =============================================================================
FRUIT_DISEASE_INFO = {
    "tomato_healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "Tomato Healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "tomato-healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "tomato_rotation": {
        "cause": "Calcium deficiency combined with moisture fluctuations and poor fruit development.",
        "effect": "Dark, sunken, leathery spots on the blossom end (bottom) of the fruit. Fruit may rot or become misshapen.",
        "pest": "None (Physiological disorder)",
        "prevention": "Maintain consistent watering schedule; ensure adequate calcium in soil; use calcium-rich fertilizers or foliar sprays; avoid over-fertilizing with nitrogen; maintain proper pH (6.0-6.8)."
    },
    "Tomato Rotation": {
        "cause": "Calcium deficiency combined with moisture fluctuations and poor fruit development.",
        "effect": "Dark, sunken, leathery spots on the blossom end (bottom) of the fruit. Fruit may rot or become misshapen.",
        "pest": "None (Physiological disorder)",
        "prevention": "Maintain consistent watering schedule; ensure adequate calcium in soil; use calcium-rich fertilizers or foliar sprays; avoid over-fertilizing with nitrogen; maintain proper pH (6.0-6.8)."
    },
    "tomato-rotation": {
        "cause": "Calcium deficiency combined with moisture fluctuations and poor fruit development.",
        "effect": "Dark, sunken, leathery spots on the blossom end (bottom) of the fruit. Fruit may rot or become misshapen.",
        "pest": "None (Physiological disorder)",
        "prevention": "Maintain consistent watering schedule; ensure adequate calcium in soil; use calcium-rich fertilizers or foliar sprays; avoid over-fertilizing with nitrogen; maintain proper pH (6.0-6.8)."
    },
    "blossom_end_rot": {
        "cause": "Calcium deficiency usually triggered by inconsistent watering or rapid growth periods.",
        "effect": "Sunken black or dark brown leathery spots at the bottom (blossom end) of the fruit. Affected area becomes hard and dry.",
        "pest": "None (Physiological Disorder - not caused by disease or pests)",
        "prevention": "Maintain steady, consistent watering (avoid drought stress followed by heavy watering); use mulch to regulate soil moisture; ensure soil has adequate calcium; avoid excessive nitrogen fertilizer; maintain soil pH between 6.0-6.8."
    },
    "Blossom End Rot": {
        "cause": "Calcium deficiency usually triggered by inconsistent watering or rapid growth periods.",
        "effect": "Sunken black or dark brown leathery spots at the bottom (blossom end) of the fruit. Affected area becomes hard and dry.",
        "pest": "None (Physiological Disorder - not caused by disease or pests)",
        "prevention": "Maintain steady, consistent watering (avoid drought stress followed by heavy watering); use mulch to regulate soil moisture; ensure soil has adequate calcium; avoid excessive nitrogen fertilizer; maintain soil pH between 6.0-6.8."
    },
    "blossom-end-rot": {
        "cause": "Calcium deficiency usually triggered by inconsistent watering or rapid growth periods.",
        "effect": "Sunken black or dark brown leathery spots at the bottom (blossom end) of the fruit. Affected area becomes hard and dry.",
        "pest": "None (Physiological Disorder - not caused by disease or pests)",
        "prevention": "Maintain steady, consistent watering (avoid drought stress followed by heavy watering); use mulch to regulate soil moisture; ensure soil has adequate calcium; avoid excessive nitrogen fertilizer; maintain soil pH between 6.0-6.8."
    },
    "yellow_leaf_curl_virus": {
        "cause": "Viral infection (Begomovirus).",
        "effect": "Stunted growth, leaves curl upward, significant yield loss.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whitefly populations; use yellow sticky traps."
    },
    "Yellow Leaf Curl Virus": {
        "cause": "Viral infection (Begomovirus).",
        "effect": "Stunted growth, leaves curl upward, significant yield loss.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whitefly populations; use yellow sticky traps."
    },
    "Tomato Yellow Leaf Curl Virus": {
        "cause": "Viral infection (Begomovirus).",
        "effect": "Stunted growth, leaves curl upward, significant yield loss.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whitefly populations; use yellow sticky traps."
    }
}

LEAF_DISEASE_INFO = {
    "healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "Healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "tomato_healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "Tomato Healthy": {
        "cause": "Optimal care, proper nutrients, and environment.",
        "effect": "Robust growth, high photosynthesis, and maximum yield.",
        "pest": "None",
        "prevention": "Continue current care and monitoring."
    },
    "spider_mites_two_spotted": {
        "cause": "Infestation by microscopic arachnids in dry, hot weather.",
        "effect": "Yellow speckling on leaves, fine silk webbing, leaf drying.",
        "pest": "Two-Spotted Spider Mites",
        "prevention": "Increase humidity; use neem oil or predatory mites."
    },
    "Spider Mites Two Spotted": {
        "cause": "Infestation by microscopic arachnids in dry, hot weather.",
        "effect": "Yellow speckling on leaves, fine silk webbing, leaf drying.",
        "pest": "Two-Spotted Spider Mites",
        "prevention": "Increase humidity; use neem oil or predatory mites."
    },
    "Tomato Spider Mites Two Spotted": {
        "cause": "Infestation by microscopic arachnids in dry, hot weather.",
        "effect": "Yellow speckling on leaves, fine silk webbing, leaf drying.",
        "pest": "Two-Spotted Spider Mites",
        "prevention": "Increase humidity; use neem oil or predatory mites."
    },
    "early_blight": {
        "cause": "Fungus (Alternaria solani).",
        "effect": "Target-like brown spots on older leaves; premature leaf drop.",
        "pest": "None (Fungal Spores)",
        "prevention": "Improve airflow; avoid overhead watering; use copper fungicide."
    },
    "Early Blight": {
        "cause": "Fungus (Alternaria solani).",
        "effect": "Target-like brown spots on older leaves; premature leaf drop.",
        "pest": "None (Fungal Spores)",
        "prevention": "Improve airflow; avoid overhead watering; use copper fungicide."
    },
    "tomato_early_blight": {
        "cause": "Fungus (Alternaria solani).",
        "effect": "Target-like brown spots on older leaves; premature leaf drop.",
        "pest": "None (Fungal Spores)",
        "prevention": "Improve airflow; avoid overhead watering; use copper fungicide."
    },
    "Tomato Early Blight": {
        "cause": "Fungus (Alternaria solani).",
        "effect": "Target-like brown spots on older leaves; premature leaf drop.",
        "pest": "None (Fungal Spores)",
        "prevention": "Improve airflow; avoid overhead watering; use copper fungicide."
    },
    "late_blight": {
        "cause": "Oomycete (Phytophthora infestans).",
        "effect": "Dark, water-soaked patches; can kill a plant in days.",
        "pest": "None (Fungal-like Pathogen)",
        "prevention": "Destroy infected plants; ensure good drainage."
    },
    "Late Blight": {
        "cause": "Oomycete (Phytophthora infestans).",
        "effect": "Dark, water-soaked patches; can kill a plant in days.",
        "pest": "None (Fungal-like Pathogen)",
        "prevention": "Destroy infected plants; ensure good drainage."
    },
    "tomato_late_blight": {
        "cause": "Oomycete (Phytophthora infestans).",
        "effect": "Dark, water-soaked patches; can kill a plant in days.",
        "pest": "None (Fungal-like Pathogen)",
        "prevention": "Destroy infected plants; ensure good drainage."
    },
    "Tomato Late Blight": {
        "cause": "Oomycete (Phytophthora infestans).",
        "effect": "Dark, water-soaked patches; can kill a plant in days.",
        "pest": "None (Fungal-like Pathogen)",
        "prevention": "Destroy infected plants; ensure good drainage."
    },
    "tomato_mosaic_virus": {
        "cause": "Viral infection spread via contact.",
        "effect": "Mottled green/yellow patterns; distorted 'fern-like' leaves.",
        "pest": "Aphids / Human Contact (Tools/Smoking)",
        "prevention": "Disinfect tools; wash hands; remove infected plants."
    },
    "Tomato Mosaic Virus": {
        "cause": "Viral infection spread via contact.",
        "effect": "Mottled green/yellow patterns; distorted 'fern-like' leaves.",
        "pest": "Aphids / Human Contact (Tools/Smoking)",
        "prevention": "Disinfect tools; wash hands; remove infected plants."
    },
    "yellow_leaf_curl_virus": {
        "cause": "Viral infection transmitted by whiteflies.",
        "effect": "Severe leaf curling and yellowing of leaf margins; stunted growth.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whiteflies with insecticides; use resistant varieties; remove infected plants."
    },
    "Yellow Leaf Curl Virus": {
        "cause": "Viral infection transmitted by whiteflies.",
        "effect": "Severe leaf curling and yellowing of leaf margins; stunted growth.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whiteflies with insecticides; use resistant varieties; remove infected plants."
    },
    "Tomato Yellow Leaf Curl Virus": {
        "cause": "Viral infection transmitted by whiteflies (Begomovirus).",
        "effect": "Severe leaf curling upward, yellowing of leaf margins, stunted growth, significant yield loss.",
        "pest": "Whiteflies (Bemisia tabaci)",
        "prevention": "Control whitefly populations with yellow sticky traps and insecticides; use resistant varieties; remove and destroy infected plants."
    },
    "septoria_leaf_spot": {
        "cause": "Septoria lycopersici fungus.",
        "effect": "Small, circular spots with grayish centers and dark borders on leaves.",
        "pest": "Fungal spores spread by splashing water",
        "prevention": "Avoid overhead watering; remove infected lower leaves; apply fungicides."
    },
    "Septoria Leaf Spot": {
        "cause": "Septoria lycopersici fungus.",
        "effect": "Small, circular spots with grayish centers and dark borders on leaves.",
        "pest": "Fungal spores spread by splashing water",
        "prevention": "Avoid overhead watering; remove infected lower leaves; apply fungicides."
    },
    "Tomato Septoria Leaf Spot": {
        "cause": "Septoria lycopersici fungus.",
        "effect": "Small, circular spots with grayish centers and dark borders on leaves.",
        "pest": "Fungal spores spread by splashing water",
        "prevention": "Avoid overhead watering; remove infected lower leaves; apply fungicides."
    },
    "bacterial_spot": {
        "cause": "Xanthomonas bacteria.",
        "effect": "Small, water-soaked spots on leaves that turn brown/black.",
        "pest": "Bacteria spread by wind and rain",
        "prevention": "Use copper-based fungicides; rotate crops; avoid overhead watering."
    },
    "Bacterial Spot": {
        "cause": "Xanthomonas bacteria.",
        "effect": "Small, water-soaked spots on leaves that turn brown/black.",
        "pest": "Bacteria spread by wind and rain",
        "prevention": "Use copper-based fungicides; rotate crops; avoid overhead watering."
    },
    "Tomato Bacterial Spot": {
        "cause": "Xanthomonas bacteria.",
        "effect": "Small, water-soaked spots on leaves that turn brown/black.",
        "pest": "Bacteria spread by wind and rain",
        "prevention": "Use copper-based fungicides; rotate crops; avoid overhead watering."
    },
    "target_spot_leaf": {
        "cause": "Fungus (Corynespora cassiicola).",
        "effect": "Small, circular spots with light brown centers and dark margins (target-like) on leaves.",
        "pest": "Fungal spores spread by air and wind.",
        "prevention": "Improve air circulation; avoid overhead watering; apply appropriate fungicides."
    },
    "Target Spot Leaf": {
        "cause": "Fungus (Corynespora cassiicola).",
        "effect": "Small, circular spots with light brown centers and dark margins (target-like) on leaves.",
        "pest": "Fungal spores spread by air and wind.",
        "prevention": "Improve air circulation; avoid overhead watering; apply appropriate fungicides."
    },
    "Tomato Target Spot Leaf": {
        "cause": "Fungus (Corynespora cassiicola).",
        "effect": "Small, circular spots with light brown centers and dark margins (target-like) on leaves.",
        "pest": "Fungal spores spread by air and wind.",
        "prevention": "Improve air circulation; avoid overhead watering; apply appropriate fungicides."
    }
}

def normalize_disease_name(disease_name):
    normalized = disease_name.lower().strip()
    
    prefixes_to_remove = ["tomato ", "tomato_", "tomato-"]
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    
    normalized = normalized.replace('-', '_').replace(' ', '_')
    
    while '__' in normalized:
        normalized = normalized.replace('__', '_')
    
    normalized = normalized.strip('_')
    
    return normalized

def get_disease_info(disease_name, normalized_key, disease_db):
    info = disease_db.get(disease_name)
    if info:
        return info
    
    info = disease_db.get(normalized_key)
    if info:
        return info
    
    info = disease_db.get(disease_name.lower())
    if info:
        return info
    
    info = disease_db.get(disease_name.lower().replace(' ', '_'))
    if info:
        return info
    
    info = disease_db.get(normalize_disease_name(disease_name))
    if info:
        return info
    
    return None

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    .main-title {
        font-size: 36px;
        font-weight: 700;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle {
        font-size: 18px;
        color: #757575;
        text-align: center;
        margin-bottom: 30px;
    }
    .helper-text {
        font-size: 14px;
        color: #9E9E9E;
        text-align: center;
        margin-top: 10px;
    }
    .healthy-badge {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .unhealthy-badge {
        background-color: #F44336;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .no-tomato-badge {
        background-color: #9E9E9E;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .disease-info-box {
        background-color: #FFF3E0;
        border-left: 5px solid #FF9800;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .disease-title {
        color: #E65100;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .recent-button {
        position: fixed;
        top: 60px;
        left: 10px;
        z-index: 999;
    }
    .recent-panel {
        background-color: white;
        border: 2px solid #2E7D32;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .scan-item {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #2E7D32;
    }
    .detection-mode-container {
        background-color: #f0f0f0;
        border-radius: 10px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# RECENT SCANS BUTTON (Top Left) - IMPROVED STYLING
# =============================================================================
st.markdown("""
<style>
    /* Custom styling for Recent Scans button */
    div[data-testid="column"]:has(button[key="recent_btn"]) button {
        background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="column"]:has(button[key="recent_btn"]) button:hover {
        background: linear-gradient(135deg, #388E3C 0%, #43A047 100%) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        transform: translateY(-2px) !important;
    }
</style>
""", unsafe_allow_html=True)

col_recent, col_spacer = st.columns([1.2, 4.3])
with col_recent:
    if st.button("📋 Recent Scans", key="recent_btn", use_container_width=True):
        st.session_state.show_recent = not st.session_state.show_recent

# =============================================================================
# RECENT SCANS PANEL (WITH DELETE FUNCTIONALITY)
# =============================================================================
if st.session_state.get('show_recent', False):
    with st.container():
        st.markdown('<div class="recent-panel">', unsafe_allow_html=True)
        st.markdown("### 📋 Recent Scans")
        
        # Ensure history is loaded
        if not st.session_state.get('history_loaded') or not st.session_state.recent_scans:
            st.session_state.recent_scans = load_user_history()
            st.session_state.history_loaded = True
        
        if len(st.session_state.recent_scans) == 0:
            st.info("No recent scans yet. Start scanning to see your history!")
        else:
            st.write(f"Showing {len(st.session_state.recent_scans)} scan(s)")
            
            for idx, scan in enumerate(st.session_state.recent_scans[:10]):  # Show last 10
                # Format date for display
                scan_date = scan.get('date', scan.get('timestamp', 'Unknown date'))
                scan_id = scan.get('scan_id', '')
                
                with st.expander(f"🍅 Scan #{len(st.session_state.recent_scans) - idx} - {scan_date}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Show saved image if available
                        img_path = scan.get('image_path')
                        if img_path and os.path.exists(img_path):
                            try:
                                st.image(img_path, caption="Scanned Image", use_column_width=True)
                            except:
                                st.write("📷 Image not available")
                        else:
                            st.write("📷 No image saved")
                    
                    with col2:
                        st.write(f"**Detection Mode:** {scan['mode']}")
                        status_emoji = "✅" if scan['status'] == 'Healthy' else "⚠️"
                        st.write(f"**Status:** {status_emoji} {scan['status']}")
                        
                        if scan.get('ripeness') and scan['ripeness'] != "N/A":
                            st.write(f"**Ripeness:** {scan['ripeness']}")
                        
                        if scan.get('diseases') and len(scan['diseases']) > 0:
                            st.write(f"**Diseases Detected:**")
                            for disease in scan['diseases']:
                                st.write(f"  • {disease}")
                        else:
                            st.write("**Diseases:** None")
                        
                        # Show scan ID for reference
                        st.caption(f"Scan ID: {scan_id[:20]}...")
                        
                        # DELETE BUTTON
                        if st.button(f"🗑️ Delete This Scan", key=f"delete_{scan_id}", type="secondary", use_container_width=True):
                            if delete_scan(scan_id):
                                st.success("✅ Scan deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete scan")
        
        if st.button("✖ Close", key="close_recent"):
            st.session_state.show_recent = False
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

# =============================================================================
# TITLE
# =============================================================================
st.markdown('<h1 class="main-title">🍅 Tomato Ripeness & Disease Checker</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Check ripeness and detect diseases in one scan</p>', unsafe_allow_html=True)

# =============================================================================
# CAMERA AND UPLOAD (WITH CAMERA TOGGLE)
# =============================================================================
st.markdown("""
<style>
    /* Camera toggle button styling */
    div[data-testid="column"]:has(button[key="toggle_camera"]) button {
        background-color: #2E7D32 !important;
        color: white !important;
        border: 1px solid #2E7D32 !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        font-size: 18px !important;
        display: flex !important;
        align-items: right !important;
        justify-content: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="column"]:has(button[key="toggle_camera"]) button:hover {
        background-color: #388E3C !important;
        border-color: #388E3C !important;
        transform: rotate(180deg) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Camera header with toggle button
    col_cam_label, col_cam_toggle = st.columns([4, 1])
    with col_cam_label:
        st.markdown('<p style="text-align: center; font-weight: 600; margin-bottom: 5px;">📸Take Photo</p>', unsafe_allow_html=True)
    with col_cam_toggle:
        if st.button("🔄", key="toggle_camera", help="Switch Camera"):
            # Toggle between front and back camera
            if st.session_state.camera_mode == "environment":
                st.session_state.camera_mode = "user"
            else:
                st.session_state.camera_mode = "environment"
            st.rerun()
    
    # Display current camera mode
    camera_mode_text = "📱 Front Camera" if st.session_state.camera_mode == "user" else "📷 Back Camera"
    st.markdown(f'<p style="text-align: center; font-size: 13px; color: #2E7D32; font-weight: 600; margin: 5px 0;">{camera_mode_text}</p>', unsafe_allow_html=True)
    
    # Camera input - note: Streamlit doesn't fully support camera selection yet
    # The toggle provides UI feedback but actual camera selection depends on browser
    camera_image = st.camera_input("Take a picture", label_visibility="collapsed")
    st.markdown('<p class="helper-text">Point camera at tomato for best results</p>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text" style="font-size: 11px; color: #FF9800;">Note: Camera selection depends on your device/browser settings</p>', unsafe_allow_html=True)
    
    st.markdown('<p style="text-align: center; margin-top: 20px; font-weight: 600;">📁 Or Upload Image</p>', unsafe_allow_html=True)
    
    # UPDATED: Added more file types (webp, bmp, tiff, jfif)
    uploaded_file = st.file_uploader(
        "Choose an image...", 
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "jfif"], 
        label_visibility="collapsed"
    )

# =============================================================================
# MODE SELECTION RADIO BUTTON
# =============================================================================
st.markdown("---")
st.markdown("<h4 style='text-align: center;'>🎯 Select Analysis Mode</h4>", unsafe_allow_html=True)

col_radio1, col_radio2, col_radio3 = st.columns([1, 2, 1])

with col_radio2:
    analysis_mode = st.radio(
        "Choose what to analyze:",
        options=["Auto-Detect (Recommended)", "Tomato Fruit Only", "Tomato Leaf Only"],
        index=0,
        help="Auto-Detect runs both models. Manual selection runs only the chosen model.",
        label_visibility="collapsed"
    )
    
    # Display help text based on selection
    if analysis_mode == "Auto-Detect (Recommended)":
        st.markdown('<p style="text-align: center; font-size: 12px; color: #757575;">AI will automatically detect and analyze both fruits and leaves</p>', unsafe_allow_html=True)
    elif analysis_mode == "Tomato Fruit Only":
        st.markdown('<p style="text-align: center; font-size: 12px; color: #FF9800;">⚠️ Will only analyze tomato fruits (ripeness & diseases)</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="text-align: center; font-size: 12px; color: #FF9800;">⚠️ Will only analyze tomato leaves (diseases)</p>', unsafe_allow_html=True)

# =============================================================================
# SUBMIT BUTTON (CENTERED)
# =============================================================================
col_center1, col_center2, col_center3 = st.columns([1, 2, 1])

with col_center2:
    # Submit Button
    st.markdown("")  # Add small space
    submit_button = st.button("🔍 Analyze Image", type="primary", use_container_width=True)

# =============================================================================
# MODEL LOADING (WITH CACHING & ERROR HANDLING)
# =============================================================================
@st.cache_resource
def load_models():
    """Load all 3 models into a central dictionary"""
    loaded_models = {}
    with st.sidebar:
        with st.status("🚀 Initializing AI Pipeline...", expanded=False) as status:
            try:
                # 1. Gatekeeper: Determines if image is Fruit, Leaf, or Invalid (used in auto-detect)
                loaded_models['gatekeeper'] = YOLO("Classifier.pt")
                
                # 2. Fruit Expert: Detection model for ripeness and diseases
                loaded_models['fruit_expert'] = YOLO("TomatoRipenessDiseasesPro.pt")
                
                # 3. Leaf Expert: Leaf detection and disease model
                loaded_models['leaf_expert'] = YOLO("TomatoLeavesDiseases.pt")
                
                st.write("✅ All 3 Models Loaded Successfully")
            except Exception as e:
                st.error(f"❌ Initialization Error: {str(e)}")
            status.update(label="🤖 Pipeline Ready", state="complete", expanded=False)
    return loaded_models

models = load_models()

# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================
def draw_boxes(image, results, detection_mode, model):
    img_pil = Image.fromarray(image) if isinstance(image, np.ndarray) else image.copy()
    draw = ImageDraw.Draw(img_pil)
    
    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf > 0.4:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cls = int(box.cls[0])
                name = model.names[cls]
                color = "#4CAF50" if name.lower() == "healthy" or name == "ripe" else "#F44336"
                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                draw.text((x1, y1-20), f"{name} {conf:.1%}", fill=color)
    return img_pil

def process(image_file, detection_mode):
    """Process image with the appropriate model based on detection mode"""
    # Select the appropriate model
    if detection_mode == "Tomato Fruit":
        model = models.get('fruit')
        if model is None:
            st.error("❌ Fruit detection model not loaded.")
            return None, None
    else:  # Tomato Leaf
        model = models.get('leaf')
        if model is None:
            st.error("❌ Leaf disease detection model not loaded.")
            return None, None
    
    image_bytes = image_file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_cv = cv2.imdecode(nparr, cv2.COLOR_BGR2RGB)
    
    mode_text = "tomato fruit ripeness & diseases" if detection_mode == "Tomato Fruit" else "tomato leaf diseases"
    with st.spinner(f"🔍 Analyzing {mode_text}..."):
        results = model.predict(source=image_cv, conf=0.5)
    
    output = draw_boxes(image_cv, results, detection_mode, model)
    return output, results

def draw_classification_result(image, result, model):
    """
    Visualize CLASSIFICATION results (not detection boxes)
    
    Args:
        image: Input image (numpy array from OpenCV)
        result: YOLO classification result with .probs attribute
        model: The classification model (for class names)
    
    Returns:
        PIL Image with classification overlay showing:
        - Colored border (green for healthy, red for diseased)
        - Top prediction with confidence
        - Semi-transparent header bar
    """
    # Convert OpenCV image (BGR) to PIL (RGB)
    if isinstance(image, np.ndarray):
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        img_pil = image.copy()
    
    # Verify this is a classification result
    if not hasattr(result, 'probs') or result.probs is None:
        # Fallback: just return the image with an error message
        draw = ImageDraw.Draw(img_pil)
        draw.text((10, 10), "Classification Error", fill='red')
        return img_pil
    
    # Get classification results
    probs = result.probs
    top_idx = int(probs.top1)
    top_conf = float(probs.top1conf)
    top_name = model.names[top_idx]
    
    # Get image dimensions
    width, height = img_pil.size
    
    # Determine color based on health status
    healthy_labels = [
        "tomato-healthy", "healthy","tomato_leaf", "tomato_healthy", "tomato healthy",
        "healthy leaf", "tomato_healthy_leaf", "healthy_leaf"
    ]
    is_healthy = top_name.lower().strip() in healthy_labels
    
    if is_healthy:
        border_color = (76, 175, 80)  # Green
        bg_color = (76, 175, 80, 200)  # Semi-transparent green
        status_text = "✓ HEALTHY"
    else:
        border_color = (244, 67, 54)  # Red
        bg_color = (244, 67, 54, 200)  # Semi-transparent red
        status_text = "⚠ DISEASE DETECTED"
    
    # Create semi-transparent overlay at the top
    overlay = Image.new('RGBA', img_pil.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Draw semi-transparent background bar at top
    bar_height = 100
    overlay_draw.rectangle([(0, 0), (width, bar_height)], fill=bg_color)
    
    # Composite the overlay onto the image
    img_rgba = img_pil.convert('RGBA')
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    img_pil = img_rgba.convert('RGB')
    
    # Now draw text on the composited image
    draw = ImageDraw.Draw(img_pil)
    
    # Try to load fonts, fallback to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        subtitle_font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            # Try another common font
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            # Ultimate fallback
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
    
    # Draw status text (centered at top)
    bbox = draw.textbbox((0, 0), status_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    status_x = (width - text_width) // 2
    draw.text((status_x, 15), status_text, fill='white', font=title_font)
    
    # Draw disease name and confidence
    disease_name = top_name.replace('_', ' ').replace('-', ' ').title()
    disease_text = f"{disease_name} ({top_conf:.1%} confidence)"
    bbox = draw.textbbox((0, 0), disease_text, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    disease_x = (width - text_width) // 2
    draw.text((disease_x, 55), disease_text, fill='white', font=subtitle_font)
    
    # Draw colored border around entire image
    border_width = 8
    for i in range(border_width):
        draw.rectangle([(i, i), (width-1-i, height-1-i)], outline=border_color, width=1)
    
    # Optional: Show top 3 predictions at bottom (if space available and height > 400)
    if height > 400 and hasattr(probs, 'top5'):
        try:
            top5_idx = probs.top5
            top5_conf = probs.top5conf
            
            # Create semi-transparent black bar at bottom
            bottom_overlay = Image.new('RGBA', img_pil.size, (255, 255, 255, 0))
            bottom_draw = ImageDraw.Draw(bottom_overlay)
            
            predictions_height = 110
            y_start = height - predictions_height
            bottom_draw.rectangle([(0, y_start), (width, height)], fill=(0, 0, 0, 180))
            
            # Composite bottom overlay
            img_rgba = img_pil.convert('RGBA')
            img_rgba = Image.alpha_composite(img_rgba, bottom_overlay)
            img_pil = img_rgba.convert('RGB')
            draw = ImageDraw.Draw(img_pil)
            
            # Draw predictions header
            draw.text((15, y_start + 5), "Top Predictions:", fill='white', font=subtitle_font)
            
            # Draw top 3
            for i in range(min(3, len(top5_idx))):
                idx = int(top5_idx[i])
                conf = float(top5_conf[i])
                name = model.names[idx].replace('_', ' ').replace('-', ' ').title()
                
                y_pos = y_start + 35 + (i * 23)
                prediction_text = f"{i+1}. {name}: {conf:.1%}"
                draw.text((20, y_pos), prediction_text, fill='white', font=small_font)
        except Exception as e:
            # If anything fails in the predictions section, just skip it
            pass
    
    return img_pil

def run_manual_mode_pipeline(image_file, models, mode):
    """
    Manual Mode Pipeline - Run only the selected model
    
    Args:
        image_file: Uploaded image file
        models: Dictionary containing all models
        mode: Either "Tomato Fruit Only" or "Tomato Leaf Only"
    
    Returns:
        tuple: (output_image, results, detection_summary)
    """
    # =========================================================================
    # IMAGE PREPROCESSING
    # =========================================================================
    try:
        img_pil = Image.open(image_file).convert("RGB")
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None, None, {"status": "error", "message": "Failed to load image"}
    
    # =========================================================================
    # RUN SELECTED MODEL ONLY
    # =========================================================================
    results = None
    detection_count = 0
    model_name = ""
    
    if mode == "Tomato Fruit Only":
        model_name = "fruit_expert"
        try:
            print("Running Fruit Detection Model (Manual Mode)...")
            results = models['fruit_expert'].predict(img_cv, conf=0.25, verbose=False)
            detection_count = len(results[0].boxes) if hasattr(results[0], 'boxes') else 0
            print(f"Fruit Model: Detected {detection_count} object(s)")
        except Exception as e:
            print(f"Fruit model error: {e}")
            
    elif mode == "Tomato Leaf Only":
        model_name = "leaf_expert"
        try:
            print("Running Leaf Detection Model (Manual Mode)...")
            results = models['leaf_expert'].predict(img_cv, conf=0.25, verbose=False)
            detection_count = len(results[0].boxes) if hasattr(results[0], 'boxes') else 0
            print(f"Leaf Model: Detected {detection_count} object(s)")
        except Exception as e:
            print(f"Leaf model error: {e}")
    
    # =========================================================================
    # CHECK IF ANYTHING WAS DETECTED
    # =========================================================================
    if detection_count == 0:
        print(f"MANUAL MODE: Nothing detected in {mode}")
        return img_cv, None, {
            'status': 'nothing_detected',
            'mode': mode,
            'count': 0
        }
    
    # =========================================================================
    # DRAW BOUNDING BOXES
    # =========================================================================
    print(f"MANUAL MODE: Detected {detection_count} object(s) in {mode}")
    
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf > 0.25:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            cls = int(box.cls[0])
            name = models[model_name].names[cls]
            
            # Color: Green for healthy/ripe, Red for diseases/unripe
            if name.lower() in ["healthy", "ripe", "tomato-healthy", "tomato_healthy"]:
                color = "#4CAF50"  # Green
            else:
                color = "#F44336"  # Red
            
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
            draw.text((x1, y1-20), f"{name} {conf:.1%}", fill=color)
    
    return img_pil, results, {
        'status': 'detected',
        'mode': mode,
        'count': detection_count
    }

def analyze_manual_results(results, mode, models):
    """
    Analyze results from manual mode (single model)
    
    Args:
        results: YOLO results from the selected model
        mode: "Tomato Fruit Only" or "Tomato Leaf Only"
        models: Model dictionary to get class names
    
    Returns:
        dict: Analysis with all detections
    """
    analysis = {
        'ripeness': None,
        'health_status': 'Healthy',
        'has_disease': False,
        'diseases': [],
        'ripeness_list': [],
        'max_conf': 0.0,
        'detections': []
    }
    
    # Define healthy labels
    HEALTHY_LABELS = [
        "tomato-healthy", "healthy", "tomato_leaf", "tomato_healthy", "tomato healthy", 
        "healthy leaf", "tomato_healthy_leaf", "healthy_leaf", "tomato healthy", "healthy tomato"
    ]
    
    # Select the appropriate model
    if mode == "Tomato Fruit Only":
        model = models['fruit_expert']
        source_type = "fruit"
    else:  # Tomato Leaf Only
        model = models['leaf_expert']
        source_type = "leaf"
    
    # =========================================================================
    # ANALYZE DETECTIONS
    # =========================================================================
    if results and len(results[0].boxes) > 0:
        print(f"Analyzing {mode} detections...")
        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf > 0.25:
                cls = int(box.cls[0])
                raw_name = model.names[cls]
                raw_name_lower = raw_name.lower().strip()
                
                print(f"  {mode}: {raw_name} ({conf:.2%})")
                
                # Track max confidence
                if conf > analysis['max_conf']:
                    analysis['max_conf'] = conf
                
                # Categorize detection
                if mode == "Tomato Fruit Only" and raw_name_lower in ["ripe", "unripe"]:
                    # Ripeness (only for fruit)
                    analysis['ripeness_list'].append({
                        "name": raw_name.title(),
                        "confidence": conf
                    })
                    analysis['detections'].append({
                        "type": "ripeness",
                        "name": raw_name,
                        "confidence": conf
                    })
                elif raw_name_lower in HEALTHY_LABELS:
                    # Healthy
                    analysis['detections'].append({
                        "type": "healthy",
                        "name": raw_name,
                        "confidence": conf
                    })
                else:
                    # Disease
                    analysis['has_disease'] = True
                    disease_entry = {
                        "name": raw_name,
                        "normalized_name": normalize_disease_name(raw_name),
                        "confidence": conf,
                        "source": source_type
                    }
                    analysis['diseases'].append(disease_entry)
                    analysis['detections'].append({
                        "type": "disease",
                        "name": raw_name,
                        "confidence": conf
                    })
    
    # =========================================================================
    # DETERMINE FINAL STATUS
    # =========================================================================
    if analysis['has_disease'] and len(analysis['diseases']) > 0:
        analysis['health_status'] = "Unhealthy"
        # Use highest disease confidence
        analysis['max_conf'] = max([d['confidence'] for d in analysis['diseases']])
        print(f"MANUAL MODE STATUS: Unhealthy - {len(analysis['diseases'])} disease(s) detected")
    else:
        analysis['health_status'] = "Healthy"
        print(f"MANUAL MODE STATUS: Healthy")
    
    # Determine ripeness (if any)
    if len(analysis['ripeness_list']) > 0:
        # Use ripeness with highest confidence
        analysis['ripeness'] = max(analysis['ripeness_list'], key=lambda x: x['confidence'])['name']
        print(f"RIPENESS: {analysis['ripeness']}")
    
    return analysis

def run_ai_pipeline(image_file, models):
    """
    NEW Dual-Detection AI Pipeline
    
    Strategy: Run BOTH fruit and leaf models on every image
    Show results from whichever model(s) detect something
    Only show "NOTHING DETECTED" if BOTH models find nothing
    
    Args:
        image_file: Uploaded image file
        models: Dictionary containing all models
    
    Returns:
        tuple: (output_image, combined_results, detection_summary)
        - output_image: Image with bounding boxes from both models
        - combined_results: Dict with 'fruit' and 'leaf' results
        - detection_summary: Dict with what was found
    """
    # =========================================================================
    # IMAGE PREPROCESSING
    # =========================================================================
    try:
        img_pil = Image.open(image_file).convert("RGB")
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None, None, {"status": "error", "message": "Failed to load image"}
    
    # =========================================================================
    # RUN BOTH MODELS
    # =========================================================================
    fruit_results = None
    leaf_results = None
    fruit_count = 0
    leaf_count = 0
    
    # Run Fruit Model
    try:
        print("Running Fruit Detection Model...")
        fruit_results = models['fruit_expert'].predict(img_cv, conf=0.25, verbose=False)
        fruit_count = len(fruit_results[0].boxes) if hasattr(fruit_results[0], 'boxes') else 0
        print(f"Fruit Model: Detected {fruit_count} object(s)")
    except Exception as e:
        print(f"Fruit model error: {e}")
    
    # Run Leaf Model
    try:
        print("Running Leaf Detection Model...")
        leaf_results = models['leaf_expert'].predict(img_cv, conf=0.25, verbose=False)
        leaf_count = len(leaf_results[0].boxes) if hasattr(leaf_results[0], 'boxes') else 0
        print(f"Leaf Model: Detected {leaf_count} object(s)")
    except Exception as e:
        print(f"Leaf model error: {e}")
    
    # =========================================================================
    # DETERMINE WHAT WAS DETECTED
    # =========================================================================
    total_detections = fruit_count + leaf_count
    
    # CASE 1: Nothing detected by either model
    if total_detections == 0:
        print("FINAL RESULT: Nothing detected by either model")
        return img_cv, {
            'fruit': fruit_results,
            'leaf': leaf_results
        }, {
            'status': 'nothing_detected',
            'fruit_count': 0,
            'leaf_count': 0
        }
    
    # CASE 2: Something was detected - draw boxes from both models
    print(f"FINAL RESULT: Detected {fruit_count} fruit(s) and {leaf_count} leaf/leaves")
    
    # Create a copy of the image to draw on
    img_with_boxes = img_cv.copy()
    img_pil = Image.fromarray(cv2.cvtColor(img_with_boxes, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Draw fruit detections (if any)
    if fruit_count > 0:
        for box in fruit_results[0].boxes:
            conf = float(box.conf[0])
            if conf > 0.25:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cls = int(box.cls[0])
                name = models['fruit_expert'].names[cls]
                
                # Color: Green for healthy/ripe, Red for diseases/unripe
                if name.lower() in ["healthy", "ripe", "tomato-healthy"]:
                    color = "#4CAF50"  # Green
                else:
                    color = "#F44336"  # Red
                
                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                draw.text((x1, y1-20), f"{name} {conf:.1%}", fill=color)
    
    # Draw leaf detections (if any)
    if leaf_count > 0:
        for box in leaf_results[0].boxes:
            conf = float(box.conf[0])
            if conf > 0.25:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cls = int(box.cls[0])
                name = models['leaf_expert'].names[cls]
                
                # Color: Green for healthy, Red for diseases
                if "healthy" in name.lower():
                    color = "#4CAF50"  # Green
                else:
                    color = "#F44336"  # Red
                
                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                draw.text((x1, y1-20), f"{name} {conf:.1%}", fill=color)
    
    return img_pil, {
        'fruit': fruit_results,
        'leaf': leaf_results
    }, {
        'status': 'detected',
        'fruit_count': fruit_count,
        'leaf_count': leaf_count
    }
    
def analyze_combined_results(combined_results, summary, models):
    """
    Analyze results from BOTH fruit and leaf models
    
    Args:
        combined_results: Dict with 'fruit' and 'leaf' YOLO results
        summary: Dict with detection counts
        models: Model dictionary to get class names
    
    Returns:
        dict: Combined analysis with all detections
    """
    analysis = {
        'ripeness': None,
        'health_status': 'Healthy',
        'has_disease': False,
        'diseases': [],
        'ripeness_list': [],
        'max_conf': 0.0,
        'fruit_detections': [],
        'leaf_detections': []
    }
    
    # Define healthy labels
    HEALTHY_LABELS = [
        "tomato-healthy", "healthy", "tomato_leaf", "tomato_healthy", "tomato healthy", 
        "healthy leaf", "tomato_healthy_leaf", "healthy_leaf", "tomato healthy", "healthy tomato"
    ]
    
    # =========================================================================
    # ANALYZE FRUIT RESULTS
    # =========================================================================
    if combined_results['fruit'] and len(combined_results['fruit'][0].boxes) > 0:
        print("Analyzing fruit detections...")
        for box in combined_results['fruit'][0].boxes:
            conf = float(box.conf[0])
            if conf > 0.25:
                cls = int(box.cls[0])
                raw_name = models['fruit_expert'].names[cls]
                raw_name_lower = raw_name.lower().strip()
                
                print(f"  Fruit: {raw_name} ({conf:.2%})")
                
                # Track max confidence
                if conf > analysis['max_conf']:
                    analysis['max_conf'] = conf
                
                # Categorize detection
                if raw_name_lower in ["ripe", "unripe"]:
                    # Ripeness
                    analysis['ripeness_list'].append({
                        "name": raw_name.title(),
                        "confidence": conf
                    })
                    analysis['fruit_detections'].append({
                        "type": "ripeness",
                        "name": raw_name,
                        "confidence": conf
                    })
                elif raw_name_lower in HEALTHY_LABELS:
                    # Healthy
                    analysis['fruit_detections'].append({
                        "type": "healthy",
                        "name": raw_name,
                        "confidence": conf
                    })
                else:
                    # Disease
                    analysis['has_disease'] = True
                    disease_entry = {
                        "name": raw_name,
                        "normalized_name": normalize_disease_name(raw_name),
                        "confidence": conf,
                        "source": "fruit"
                    }
                    analysis['diseases'].append(disease_entry)
                    analysis['fruit_detections'].append({
                        "type": "disease",
                        "name": raw_name,
                        "confidence": conf
                    })
    
    # =========================================================================
    # ANALYZE LEAF RESULTS
    # =========================================================================
    if combined_results['leaf'] and len(combined_results['leaf'][0].boxes) > 0:
        print("Analyzing leaf detections...")
        for box in combined_results['leaf'][0].boxes:
            conf = float(box.conf[0])
            if conf > 0.25:
                cls = int(box.cls[0])
                raw_name = models['leaf_expert'].names[cls]
                raw_name_lower = raw_name.lower().strip()
                
                print(f"  Leaf: {raw_name} ({conf:.2%})")
                
                # Track max confidence
                if conf > analysis['max_conf']:
                    analysis['max_conf'] = conf
                
                # Categorize detection
                if raw_name_lower in HEALTHY_LABELS:
                    # Healthy
                    analysis['leaf_detections'].append({
                        "type": "healthy",
                        "name": raw_name,
                        "confidence": conf
                    })
                else:
                    # Disease
                    analysis['has_disease'] = True
                    disease_entry = {
                        "name": raw_name,
                        "normalized_name": normalize_disease_name(raw_name),
                        "confidence": conf,
                        "source": "leaf"
                    }
                    analysis['diseases'].append(disease_entry)
                    analysis['leaf_detections'].append({
                        "type": "disease",
                        "name": raw_name,
                        "confidence": conf
                    })
    
    # =========================================================================
    # DETERMINE FINAL STATUS
    # =========================================================================
    if analysis['has_disease'] and len(analysis['diseases']) > 0:
        analysis['health_status'] = "Unhealthy"
        # Use highest disease confidence
        analysis['max_conf'] = max([d['confidence'] for d in analysis['diseases']])
        print(f"FINAL STATUS: Unhealthy - {len(analysis['diseases'])} disease(s) detected")
    else:
        analysis['health_status'] = "Healthy"
        print(f"FINAL STATUS: Healthy")
    
    # Determine ripeness (if any)
    if len(analysis['ripeness_list']) > 0:
        # Use ripeness with highest confidence
        analysis['ripeness'] = max(analysis['ripeness_list'], key=lambda x: x['confidence'])['name']
        print(f"RIPENESS: {analysis['ripeness']}")
    
    return analysis

# =============================================================================
# LOAD USER HISTORY ON LOGIN (MOVED HERE - AFTER FUNCTION DEFINITIONS)
# =============================================================================
if st.session_state.get('logged_in') and not st.session_state.get('history_loaded'):
    # Load history from file when user logs in
    st.session_state.recent_scans = load_user_history()
    st.session_state.history_loaded = True
    # Store username to detect if user changes
    st.session_state.loaded_for_user = st.session_state.get('username')
elif st.session_state.get('logged_in') and st.session_state.get('history_loaded'):
    # Check if user changed (logout/login as different user)
    current_user = st.session_state.get('username')
    if st.session_state.get('loaded_for_user') != current_user:
        # Reload history for new user
        st.session_state.recent_scans = load_user_history()
        st.session_state.loaded_for_user = current_user

# =============================================================================
# MAIN LOGIC - With Manual Mode Selection Support
# =============================================================================
if submit_button and (camera_image or uploaded_file):
    input_image = camera_image if camera_image else uploaded_file
    
    # =============================================================================
    # ROUTE BASED ON SELECTED MODE
    # =============================================================================
    
    # MANUAL MODE: User selected specific model
    if analysis_mode in ["Tomato Fruit Only", "Tomato Leaf Only"]:
        st.info(f"🎯 Running in Manual Mode: {analysis_mode}")
        
        # Run manual mode pipeline
        output_image, results, summary = run_manual_mode_pipeline(input_image, models, analysis_mode)
        
        # CASE 1: Nothing detected
        if summary['status'] == 'nothing_detected':
            st.markdown("---")
            st.markdown("<h2 style='text-align: center;'>Analysis Result</h2>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(input_image, caption="Original Image", use_container_width=True)
            with col2:
                st.image(output_image, caption="AI Detection Result", use_container_width=True)
            
            st.markdown("---")
            st.markdown("<h3 style='text-align: center;'>Status</h3>", unsafe_allow_html=True)
            col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
            with col_status2:
                st.markdown("<div style='text-align: center;'><span class='no-tomato-badge'>❌ NOTHING DETECTED</span></div>", unsafe_allow_html=True)
                if analysis_mode == "Tomato Fruit Only":
                    st.markdown("<p style='text-align: center; color: #757575;'>No tomato fruit detected in the image. The image may contain a leaf or other object.</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='text-align: center; color: #757575;'>No tomato leaf detected in the image. The image may contain a fruit or other object.</p>", unsafe_allow_html=True)
        
        # CASE 2: Something detected in manual mode
        elif summary['status'] == 'detected':
            # Analyze what was found
            analysis = analyze_manual_results(results, analysis_mode, models)
            
            # Save to history
            if hasattr(input_image, 'seek'):
                input_image.seek(0)
            save_scan_to_history(
                mode=analysis_mode,
                status=analysis['health_status'],
                ripeness=analysis['ripeness'],
                diseases=analysis['diseases'],
                image_file=input_image
            )
            
            # Display results
            st.markdown("---")
            st.markdown("<h2 style='text-align: center;'>Analysis Result</h2>", unsafe_allow_html=True)
            
            # Show images
            col1, col2 = st.columns(2)
            with col1:
                st.image(input_image, caption="Original Image", use_container_width=True)
            with col2:
                st.image(output_image, caption="AI Detection Result", use_container_width=True)
            
            st.markdown("---")
            
            # Display Health Status
            st.markdown("<h3 style='text-align: center;'>Status</h3>", unsafe_allow_html=True)
            col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
            
            with col_status2:
                if analysis['health_status'] == "Healthy":
                    st.markdown(f"<div style='text-align: center;'><span class='healthy-badge'>✅ HEALTHY ({analysis['max_conf']:.1%})</span></div>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; color: #4CAF50;'>No diseases detected!</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center;'><span class='unhealthy-badge'>⚠️ UNHEALTHY ({analysis['max_conf']:.1%})</span></div>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; color: #F44336;'>Disease(s) detected!</p>", unsafe_allow_html=True)
            
            # Display Ripeness (if fruit mode and ripeness detected)
            if analysis_mode == "Tomato Fruit Only" and analysis['ripeness']:
                st.markdown("<h3 style='text-align: center; margin-top: 20px;'>Ripeness</h3>", unsafe_allow_html=True)
                col_ripe1, col_ripe2, col_ripe3 = st.columns([1, 2, 1])
                with col_ripe2:
                    if analysis['ripeness'] == "Ripe":
                        st.success(f"🍅 **{analysis['ripeness']}** - Ready to harvest/eat!")
                    else:
                        st.warning(f"🍅 **{analysis['ripeness']}** - Not ready yet, needs more time!")
            
            # Display Disease Information
            if analysis['has_disease'] and analysis['diseases']:
                st.markdown("---")
                st.markdown("<h3 style='color: #F44336;'>🦠 Disease Information</h3>", unsafe_allow_html=True)
                
                for disease in analysis['diseases']:
                    disease_name = disease["name"]
                    normalized_key = disease.get("normalized_name", normalize_disease_name(disease_name))
                    conf = disease["confidence"]
                    source = disease.get("source", "unknown")
                    
                    # Choose database based on source
                    disease_db = FRUIT_DISEASE_INFO if source == "fruit" else LEAF_DISEASE_INFO
                    
                    # Lookup disease info with comprehensive fallbacks
                    info = get_disease_info(disease_name, normalized_key, disease_db)
                    display_name = disease_name.replace('-', ' ').replace('_', ' ').title()
                    source_icon = "🍅" if source == "fruit" else "🌿"
                    
                    with st.expander(f"{source_icon} {display_name} ({conf:.1%} confidence)", expanded=True):
                        if info:
                            pest_text = info.get('pest', 'None identified')
                            if not pest_text or pest_text.lower() in ['none', 'none identified']:
                                pest_display = "🌿 <b>External Factors:</b><br>Environmental conditions or soil factors"
                            else:
                                pest_display = f"🐜 <b>Pest/Vector:</b><br>{pest_text}"
                            
                            st.markdown(f"""
                                <div class="disease-info-box">
                                    <div class="disease-title">{display_name}</div>
                                    <p>🔬 <b>Cause:</b><br>{info.get('cause', 'N/A')}</p>
                                    <p>⚠️ <b>Effect:</b><br>{info.get('effect', 'N/A')}</p>
                                    <p>{pest_display}</p>
                                    <p>🛡️ <b>Prevention/Treatment:</b><br>{info.get('prevention', 'N/A')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"⚠️ No detailed info available for '{display_name}'.")
            
            # Detection Summary
            st.markdown("---")
            st.markdown("<h4>Detection Summary:</h4>", unsafe_allow_html=True)
            st.info(f"🎯 **Manual Mode:** {analysis_mode}")
            st.info(f"📊 **Detected {summary['count']} object(s)**")
            for detection in analysis['detections']:
                if detection['type'] == 'ripeness':
                    st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")
                elif detection['type'] == 'disease':
                    st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")
                elif detection['type'] == 'healthy':
                    st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")
    
    # AUTO-DETECT MODE: Run both models
    else:  # analysis_mode == "Auto-Detect (Recommended)"
        # Run BOTH models on the image
        output_image, combined_results, summary = run_ai_pipeline(input_image, models)
        
        # CASE 1: Nothing detected by either model
        if summary['status'] == 'nothing_detected':
            st.markdown("---")
            st.markdown("<h2 style='text-align: center;'>Analysis Result</h2>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(input_image, caption="Original Image", use_container_width=True)
            with col2:
                st.image(output_image, caption="AI Detection Result", use_container_width=True)
            
            st.markdown("---")
            st.markdown("<h3 style='text-align: center;'>Status</h3>", unsafe_allow_html=True)
            col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
            with col_status2:
                st.markdown("<div style='text-align: center;'><span class='no-tomato-badge'>❌ NOTHING DETECTED</span></div>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #757575;'>No tomato fruit or leaf detected in the image.</p>", unsafe_allow_html=True)
        
        # CASE 2: Something was detected
        elif summary['status'] == 'detected':
            # Analyze what was found
            analysis = analyze_combined_results(combined_results, summary, models)
            
            # Determine mode for history saving
            if summary['fruit_count'] > 0 and summary['leaf_count'] > 0:
                mode_for_history = "Fruit & Leaf"
            elif summary['fruit_count'] > 0:
                mode_for_history = "Tomato Fruit"
            else:
                mode_for_history = "Tomato Leaf"
            
            # Save to history
            if hasattr(input_image, 'seek'):
                input_image.seek(0)
            save_scan_to_history(
                mode=mode_for_history,
                status=analysis['health_status'],
                ripeness=analysis['ripeness'],
                diseases=analysis['diseases'],
                image_file=input_image
            )
            
            # Display results
            st.markdown("---")
            st.markdown("<h2 style='text-align: center;'>Analysis Result</h2>", unsafe_allow_html=True)
            
            # Show images
            col1, col2 = st.columns(2)
            with col1:
                st.image(input_image, caption="Original Image", use_container_width=True)
            with col2:
                st.image(output_image, caption="AI Detection Result", use_container_width=True)
            
            st.markdown("---")
            
            # Display Health Status
            st.markdown("<h3 style='text-align: center;'>Status</h3>", unsafe_allow_html=True)
            col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
            
            with col_status2:
                if analysis['health_status'] == "Healthy":
                    st.markdown(f"<div style='text-align: center;'><span class='healthy-badge'>✅ HEALTHY ({analysis['max_conf']:.1%})</span></div>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; color: #4CAF50;'>No diseases detected!</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center;'><span class='unhealthy-badge'>⚠️ UNHEALTHY ({analysis['max_conf']:.1%})</span></div>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; color: #F44336;'>Disease(s) detected!</p>", unsafe_allow_html=True)
            
            # Display Ripeness (if any fruit detected)
            if analysis['ripeness']:
                st.markdown("<h3 style='text-align: center; margin-top: 20px;'>Ripeness</h3>", unsafe_allow_html=True)
                col_ripe1, col_ripe2, col_ripe3 = st.columns([1, 2, 1])
                with col_ripe2:
                    if analysis['ripeness'] == "Ripe":
                        st.success(f"🍅 **{analysis['ripeness']}** - Ready to harvest/eat!")
                    else:
                        st.warning(f"🍅 **{analysis['ripeness']}** - Not ready yet, needs more time!")
            
            # Display Disease Information
            if analysis['has_disease'] and analysis['diseases']:
                st.markdown("---")
                st.markdown("<h3 style='color: #F44336;'>🦠 Disease Information</h3>", unsafe_allow_html=True)
                
                for disease in analysis['diseases']:
                    disease_name = disease["name"]
                    normalized_key = disease.get("normalized_name", normalize_disease_name(disease_name))
                    conf = disease["confidence"]
                    source = disease.get("source", "unknown")
                    
                    # Choose database based on source
                    disease_db = FRUIT_DISEASE_INFO if source == "fruit" else LEAF_DISEASE_INFO
                    
                    # Lookup disease info with comprehensive fallbacks
                    info = get_disease_info(disease_name, normalized_key, disease_db)
                    display_name = disease_name.replace('-', ' ').replace('_', ' ').title()
                    source_icon = "🍅" if source == "fruit" else "🌿"
                    
                    with st.expander(f"{source_icon} {display_name} ({conf:.1%} confidence)", expanded=True):
                        if info:
                            pest_text = info.get('pest', 'None identified')
                            if not pest_text or pest_text.lower() in ['none', 'none identified']:
                                pest_display = "🌿 <b>External Factors:</b><br>Environmental conditions or soil factors"
                            else:
                                pest_display = f"🐜 <b>Pest/Vector:</b><br>{pest_text}"
                            
                            st.markdown(f"""
                                <div class="disease-info-box">
                                    <div class="disease-title">{display_name}</div>
                                    <p>🔬 <b>Cause:</b><br>{info.get('cause', 'N/A')}</p>
                                    <p>⚠️ <b>Effect:</b><br>{info.get('effect', 'N/A')}</p>
                                    <p>{pest_display}</p>
                                    <p>🛡️ <b>Prevention/Treatment:</b><br>{info.get('prevention', 'N/A')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"⚠️ No detailed info available for '{display_name}'.")
            
            # Detection Summary
            st.markdown("---")
            st.markdown("<h4>Detection Summary:</h4>", unsafe_allow_html=True)
            
            # Show what was detected
            if summary['fruit_count'] > 0:
                st.info(f"🍅 **Detected {summary['fruit_count']} fruit detection(s)**")
                for detection in analysis['fruit_detections']:
                    if detection['type'] == 'ripeness':
                        st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")
                    elif detection['type'] == 'disease':
                        st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")
            
            if summary['leaf_count'] > 0:
                st.info(f"🌿 **Detected {summary['leaf_count']} leaf detection(s)**")
                for detection in analysis['leaf_detections']:
                    if detection['type'] == 'disease':
                        st.write(f"  • {detection['name']} ({detection['confidence']:.1%})")


elif submit_button and not (camera_image or uploaded_file):
    st.warning("⚠️ Please capture or upload an image before analyzing!")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: #9E9E9E;'>Powered by YOLOv8 | Ripeness & Disease Detection</p>", unsafe_allow_html=True)