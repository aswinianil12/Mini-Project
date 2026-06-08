# app.py
import streamlit as st
import pandas as pd
import os
import io
import base64
import time
import hashlib
from PIL import Image
from utils.predict import predict_disease
# Files
csv_file = 'users.csv'
history_file = 'history.csv'
UPLOADS_DIR = "uploads"

# Ensure folders/files
os.makedirs(UPLOADS_DIR, exist_ok=True)
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["username", "password", "email"]).to_csv(csv_file, index=False)
if not os.path.exists(history_file):
    pd.DataFrame(columns=["username", "image_path", "disease", "tip", "file_hash", "timestamp"]).to_csv(history_file, index=False)

# ---------------- helpers ----------------
def load_users():
    return pd.read_csv(csv_file)

def add_user(username, password, email):
    new_user = pd.DataFrame([[username, password, email]], columns=["username", "password", "email"])
    new_user.to_csv(csv_file, mode='a', header=False, index=False)

def update_password(username, new_password):
    users = load_users()
    users.loc[users['username'] == username, 'password'] = new_password
    users.to_csv(csv_file, index=False)

def save_history(username, image_path, disease, tip, file_hash):
    if os.path.exists(history_file):
        df = pd.read_csv(history_file)
    else:
        df = pd.DataFrame(columns=["username", "image_path", "disease", "tip", "file_hash", "timestamp"])

    exists = ((df['username'] == username) & (df['file_hash'] == file_hash)).any()
    if not exists:
        row = pd.DataFrame([[username, image_path, disease, tip, file_hash, int(time.time())]],
                           columns=df.columns)
        row.to_csv(history_file, mode='a', header=not os.path.exists(history_file), index=False)

def get_user_history(username):
    if not os.path.exists(history_file):
        return pd.DataFrame(columns=["username", "image_path", "disease", "tip", "file_hash", "timestamp"])
    df = pd.read_csv(history_file)
    return df[df["username"] == username].sort_values("timestamp", ascending=False)

# ---------------- UI helpers ----------------
def add_home_bg(image_file):
    import base64
    import os
    if os.path.exists(image_file):
        with open(image_file, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url("data:image/png;base64,{encoded}") no-repeat center center fixed;
                background-size: cover;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"⚠ Background image not found: {image_file}")

# ---------------- session ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_file_hash" not in st.session_state:
    st.session_state.last_file_hash = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ================= FOOTER =================
def show_footer():
    st.markdown(
        '<div class="footer">© 2025 Fruit Disease Detection System | All Rights Reserved</div>',
        unsafe_allow_html=True
    )



# ---------------- Sidebar Navigation ----------------
# ---------------- TOP NAVIGATION BAR ----------------
def show_navbar():
    st.markdown("""
        <style>
        .navbar {
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(90deg, #ffb347, #ffcc33);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        }
        .navbar a {
            text-decoration: none;
            color: white;
            font-weight: 600;
            font-size: 17px;
            margin: 0 20px;
            padding: 8px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-family: 'Segoe UI', sans-serif;
        }
        .navbar a:hover {
            background-color: rgba(255, 255, 255, 0.25);
        }
        .active {
            background-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    # Define pages based on login state
    if st.session_state.get("logged_in", False):
        pages = ["Home", "Profile", "About", "Logout"]
    else:
        pages = ["Home", "Login", "Register", "About"]

    # Create equal-width columns for buttons
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        # ✅ Each button now has a unique key
        if cols[i].button(p, key=f"nav_{p}"):
            st.session_state.page = p



# ✅ Initialize and show navbar
if "page" not in st.session_state:
    st.session_state.page = "Home"

show_navbar()
page = st.session_state.page
# ---------------- Home ----------------
if page == "Home":
    # Set background
    add_home_bg("homee.jpg")
    
    st.markdown("<h2 style='color:yellow; text-align:center;'>🍎 Fruit Disease Detection System</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:white;'>From Sick to Safe: Instant Fruit Disease Diagnosis & Tips.</p>", unsafe_allow_html=True)

    if st.session_state.logged_in:
        # Initialize session variables
        if "last_file_hash" not in st.session_state:
            st.session_state.last_file_hash = None
        if "last_result" not in st.session_state:
            st.session_state.last_result = None

        # Welcome message
        st.markdown(f"<h3 style='color:yellow; text-align:center;'>👋 Welcome, {st.session_state.username}!</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:white;'>Detect diseases in <b>Guava</b>, <b>Pomegranate</b>, and <b>Mango</b>.</p>", unsafe_allow_html=True)

        # Fruit selection
        fruit_type = st.selectbox("🍊 Select the fruit type before uploading:", ["Select Fruit", "Pomegranate", "Guava", "Mango"])
        
        if fruit_type != "Select Fruit":
            uploaded_file = st.file_uploader(f"📤 Upload a {fruit_type} image", type=["jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                # Check if already processed in this session
                if st.session_state.last_file_hash == file_hash and st.session_state.last_result:
                    st.markdown(f"""
                            <div style='background-color:yellow; color:black; padding:10px; border:2px solid black; border-radius:5px;'>
                                <p style='font-size:18px;'>⚠ This file was already processed in this session.</p>
                                
                            </div>
                        """, unsafe_allow_html=True)
                    
                    if st.button("🔍 View Previous Result"):
                        prev = st.session_state.last_result
                        st.image(prev['image_path'], caption=f"Previously Uploaded {fruit_type} Image", use_container_width=True)
                        st.markdown(f"""
                            <div style='background-color:yellow; color:black; padding:10px; border:2px solid black; border-radius:5px;'>
                                <p style='font-size:18px;'>✅ Predicted Disease: <b>{prev['label']}</b></p>
                                <p style='font-size:16px;'>💡 Prevention Tip: {prev['tip']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    # Open and resize uploaded image
                    # Open uploaded image
                    img = Image.open(io.BytesIO(file_bytes))

                    # Convert to RGB if PNG with alpha channel
                    if img.mode in ("RGBA", "P"):
                     img = img.convert("RGB")

                    # Resize image to smaller dimensions
                    max_size = (256, 256)  # reduce size
                    img.thumbnail(max_size)  # keeps aspect ratio

                    # Save resized image with lower quality
                    unique_name = f"{st.session_state.username}{int(time.time())}{file_hash[:8]}.jpg"
                    temp_path = os.path.join(UPLOADS_DIR, unique_name)
                    img.save(temp_path, optimize=True, quality=70)

                    # Display uploaded image
                    st.image(img, caption=f"Uploaded {fruit_type} Image", use_container_width=True)

                    # Predict disease
                    try:
                        label, tip, confidence = predict_disease(temp_path)
                    except Exception as e:
                        st.error(f"Prediction error: {e}")
                        save_history(st.session_state.username, temp_path, "PredictionError", str(e), file_hash)
                        st.session_state.last_file_hash = file_hash
                        st.session_state.last_result = {"label": "PredictionError", "tip": str(e), "image_path": temp_path, "confidence": 0}
                    else:
                        # Validate fruit type
                        if fruit_type.lower() not in label.lower():
                            st.error(f"⚠ Please upload a valid {fruit_type} image. Detected: {label} (confidence {confidence:.2f})")
                        else:
                            st.markdown(f"""
                                <div style='background-color:yellow; color:black; padding:10px; border:2px solid black; border-radius:5px;'>
                                    <p style='font-size:18px;'>✅ Predicted Disease: <b>{label}</b></p>
                                    <p style='font-size:16px;'>💡 Prevention Tip: {tip}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        # Save to history
                        save_history(st.session_state.username, temp_path, label, tip, file_hash)

                        # Update session state
                        st.session_state.last_file_hash = file_hash
                        st.session_state.last_result = {"label": label, "tip": tip, "image_path": temp_path, "confidence": confidence}

        else:
            st.warning("👆 Please select a fruit type first before uploading the image.")
    else:
        st.warning("⚠ Please login to upload a fruit image.")
# ---------------- Dashboard ----------------
elif page == "Profile":
    add_home_bg("homee.jpg")
    if st.session_state.logged_in:
        st.markdown("<h2 style='color:white; text-align:center;'>👤 User Profile</h2>", unsafe_allow_html=True)
        users = load_users()
        user = users[users['username'] == st.session_state.username].iloc[0]
        
        st.markdown(f"### Username: {user['username']}")
        st.markdown(f"### Email: {user['email']}")
        st.markdown("### Password: 🔒 (Hidden)")

        with st.expander("🔑 Change Password"):
            new_password = st.text_input("Enter new password", type="password")
            if st.button("Update Password"):
                if new_password.strip() == "":
                    st.warning("Enter a non-empty password.")
                else:
                    update_password(user['username'], new_password)
                    st.success("Password updated successfully!")

        st.markdown("---")


        # --- Upload History ---
        history_df = get_user_history(user['username'])
        if not history_df.empty:
            for _, row in history_df.iterrows():
                img_path = row["image_path"]
                disease = row.get("disease", "Unknown")
                tip = row.get("tip", "")
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row['timestamp']))

                with st.container():
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if os.path.exists(img_path):
                            st.image(img_path, width=180, caption="Uploaded Image")
                    with col2:
                        st.markdown(f"""
                            <div style='background-color:#fff8e1; border-left:5px solid #ff9800;
                                        padding:10px 15px; border-radius:10px; box-shadow:0px 2px 6px rgba(0,0,0,0.1);'>
                                <p style='font-size:17px; color:#333; margin-bottom:5px;'>
                                    <b>🩺 Disease:</b> {disease}
                                </p>
                                <p style='font-size:15px; color:#444; margin-bottom:5px;'>
                                    <b>💡 Tip:</b> {tip}
                                </p>
                                <p style='font-size:13px; color:#666;'>🕒 <i>{timestamp}</i></p>
                            </div>
                        """, unsafe_allow_html=True)

                st.markdown("<hr style='margin:10px 0; border:1px solid #ddd;'>", unsafe_allow_html=True)
        else:
            st.info("No upload history yet.")
    else:
        st.error("⚠ Please login first to access your Profile.")
# ---------------- Login ----------------
elif page == "Login":
    st.subheader("🔐 Login")

    # Track if user clicked "Forgot Password"
    if "forgot_password" not in st.session_state:
        st.session_state.forgot_password = False

    if not st.session_state.forgot_password:
        # Normal login
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type='password', key="login_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                users = load_users()
                match = users[(users['username'] == username) & (users['password'] == password)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.page = "Home"
                    st.success(f"Welcome, {username}!")
                else:
                    st.error("Invalid username or password.")
        with col2:
            if st.button("Forgot Password?"):
                st.session_state.forgot_password = True

    else:
        # Forgot password form
        st.warning("🔑 Reset your password")
        username_fp = st.text_input("Enter your username", key="fp_username")
        new_password = st.text_input("Enter new password", type='password', key="fp_new_password")
        confirm_password = st.text_input("Confirm new password", type='password', key="fp_confirm_password")

        if st.button("Update Password"):
            users = load_users()
            if username_fp not in users['username'].values:
                st.error("Username not found.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif new_password.strip() == "":
                st.error("Password cannot be empty.")
            else:
                update_password(username_fp, new_password)
                st.success("Password updated successfully! Please login with your new password.")
                # Reset forgot password state
                st.session_state.forgot_password = False
# ---------------- Register ----------------
elif page == "Register":
    st.subheader("📝 Register")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type='password')
    email = st.text_input("Email")
    if st.button("Register"):
        users = load_users()
        if username in users['username'].values:
            st.warning("Username already exists.")
        else:
            add_user(username, password, email)
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.page = "Home"  # Redirect
            st.success("Registration successful! You are now logged in.")

# ---------------- About ----------------
elif page == "About":
    st.markdown("<h2 style='color:white; text-align:center;'>👤 About</h2>", unsafe_allow_html=True)
    st.markdown("""
    This system detects fruit diseases using a Convolutional Neural Network (CNN).  
    It supports Guava, Pomegranate, and Mango, providing prevention tips for each detected disease.

    Features:
    - Upload fruit images of Guava, Mango and Pomegranate and get instant disease predictions  
    - Save and view previous uploads in Profile  
    - Secure login and password management  
    """)
    st.markdown("📧 support@fruitdetection.com | 📱 +91 98765 43210 | 🌐 www.fruitdetection.com")

# ---------------- Logout ----------------
elif page == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "Home"  # Redirect
    st.success("You have been logged out successfully.")

# ================= FOOTER =================
show_footer()