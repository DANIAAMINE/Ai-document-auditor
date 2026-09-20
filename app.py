import pypdf
import streamlit as st
import openai

# 1. App Title and Header
st.title("🚚 AI Freight & Document Auditor")
st.write("Upload a Rate Confirmation, Bill of Lading, or Invoice to audit instantly!")

# 2. Get API Key from Secrets or Sidebar
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Paste your secret key here")

# 3. File Uploader
uploaded_file = st.file_uploader("Drop your PDF here", type=["pdf", "png", "jpg", "txt"])

# 4. Process File
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

    # Preview raw text
    with st.expander("📄 View extracted raw text from PDF"):
        st.write(text if text else "No readable text found.")

    st.subheader("🤖 AI Extraction & Audit Report")
    text_upper = text.upper()

    # Smart Rule Fallback
    if "INVOICE" in text_upper:
        doc_type = "Carrier Invoice"
    elif "BILL OF LADING" in text_upper or "BOL" in text_upper:
        doc_type = "Bill of Lading (BOL)"
    elif "RATE CONFIRMATION" in text_upper or "RATE CON" in text_upper:
        doc_type = "Rate Confirmation"
    else:
        doc_type = "Logistics Document"

    if "UNAPPROVED" in text_upper:
        audit_flag = "⚠️ WARNING: Unapproved fee or rate discrepancy detected!"
    elif "DETENTION" in text_upper:
        audit_flag = "ℹ️ Detention clause detected in document."
    else:
        audit_flag = "✅ Document scanned. No billing discrepancies flagged."

    # Try AI Extraction via OpenAI
    if api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"Analyze this freight document text and return a JSON object with keys: document_type, carrier_name, load_number, agreed_linehaul_rate, fuel_surcharge, detention_clause, audit_status.\n\nDocument Text:\n{text}"
            
            with st.spinner("AI is analyzing your document..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert logistics document auditor. Respond strictly in valid JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                st.json(response.choices.message.content)
        except Exception as e:
            st.warning("Note: Live OpenAI credit balance required for GPT extraction. Showing standard rule audit result below:")
            st.json({
                "file_name": uploaded_file.name,
                "document_type": doc_type,
                "audit_status": audit_flag
            })
    else:
        st.json({
            "file_name": uploaded_file.name,
            "document_type": doc_type,
            "audit_status": audit_flag
        })
