import pypdf
import streamlit as st

# 1. Title and Header
st.title("🚚 AI Freight & Document Auditor")
st.write(
    "Upload a Rate Confirmation, Bill of Lading, or Invoice to audit"
    " instantly!"
)

# 2. Drag and Drop File Uploader
uploaded_file = st.file_uploader(
    "Drop your PDF here", type=["pdf", "png", "jpg", "txt"]
)

# 3. Read the ACTUAL contents of the uploaded PDF
if uploaded_file is not None:
    st.success(f"✅ Received file: {uploaded_file.name}")
    text = ""
    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            text = uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Error reading file: {e}")

    # Preview extracted text
    with st.expander("📄 Click to view extracted raw text from your file"):
        st.write(text if text else "No readable text found.")

    # 4. Smart Document Identification & Audit Rules
    st.subheader("🤖 AI Extraction & Audit Report")
    text_upper = text.upper()

    # Identify Document Type dynamically
    if "INVOICE" in text_upper:
        doc_type = "Carrier Invoice"
    elif "BILL OF LADING" in text_upper or "BOL" in text_upper:
        doc_type = "Bill of Lading (BOL)"
    elif "RATE CONFIRMATION" in text_upper or "RATE CON" in text_upper:
        doc_type = "Rate Confirmation"
    else:
        doc_type = "Logistics Document"

    # Smart Audit Flag detection
    if "UNAPPROVED" in text_upper:
        audit_flag = (
            "⚠️ WARNING: Unapproved fee or rate discrepancy detected in invoice!"
        )
    elif "DETENTION" in text_upper:
        audit_flag = "ℹ️ Detention clause detected in document."
    else:
        audit_flag = "✅ Document scanned. No billing discrepancies flagged."

    # Display the dynamic results
    extracted_data = {
        "file_name": uploaded_file.name,
        "document_type": doc_type,
        "audit_status": audit_flag,
    }
    st.json(extracted_data)
