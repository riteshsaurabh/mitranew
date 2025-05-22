import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Money-Mitra - Minimal Test",
    page_icon="💰",
    layout="wide"
)

# Main App
st.title("Money-Mitra Finance Dashboard")
st.write("This is a minimal test version to diagnose deployment issues.")

# Basic input
symbol = st.text_input("Enter a stock symbol (e.g., AAPL):", "AAPL")
st.write(f"You entered: {symbol}")

# Simple button
if st.button("Click me"):
    st.success("Button clicked!")

# Footer
st.markdown("---")
st.caption("Money-Mitra - Minimal Test App") 