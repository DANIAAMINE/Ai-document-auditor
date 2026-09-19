import streamlit as st

# 1. Paint the Title on the screen
st.title("🚚 AI Freight & Document Auditor")
st.write("Upload a Rate Confirmation or Bill of Lading (BOL) to audit instantly!")

# 2. Create the file drop box
uploaded_file = st.file_uploader("Drop your PDF or Image here", type=["pdf", "png", "jpg"])

# 3. Show the magic AI extraction when a file is uploaded
if uploaded_file is not None:
    st.success(f"✅ Received file: {uploaded_file.name}")
    st.subheader("🤖 AI Extraction & Audit Report")

    # Sample extracted JSON data
    sample_data = {
        "document_type": "Rate Confirmation",
        "carrier_name": "Express Freight LLC",
        "load_number": "LOAD-88231",
        "agreed_rate": "$2,400.00",
        "detected_detention_clause": "$50/hr after 2 hours",
        "audit_flag": "⚠️ WARNING: Unapproved $150 Fuel Surcharge Detected!"
    }

    st.json(sample_data)
