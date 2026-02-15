import streamlit as st
import numpy as np
from PIL import Image
import datetime
import json
import os

# Simple test app without OpenCV or YOLO
st.set_page_config(
    page_title="Tomato AI Test",
    page_icon="🍅",
    layout="centered"
)

st.title("🍅 Tomato AI Test App")
st.write("This is a test to verify basic deployment works!")

# Test basic functionality
if st.button("Test Button"):
    st.success("✅ Button works!")
    st.write(f"Current time: {datetime.now()}")

# Test file operations
if st.button("Test File Operations"):
    try:
        test_data = {"test": "data", "timestamp": str(datetime.now())}
        with open("test.json", "w") as f:
                json.dump(test_data, f)
        st.success("✅ File operations work!")
        os.remove("test.json")
    except Exception as e:
        st.error(f"❌ File error: {e}")

st.write("If you see this, basic Streamlit deployment is working!")
st.write("Next step: Add OpenCV and YOLO gradually")
