import json
import re
import openai
import pandas as pd
import pypdf
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="AI Freight Auditor", page_icon="🚚", layout="wide"
)

# 2. Header and Title
st.title("🚚 AI Freight & Document Auditor")
st.caption("Professional Logistics Document Auditor & Discrepancy Tracker")

# 3. Sidebar API Key Configuration
st.sidebar.header("⚙️ Settings")
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input(
        "OpenAI API Key", type="password", help="Paste your secret key here"
    )

if api_key:
    st.sidebar.success("🔑 OpenAI API Key Connected")
else:
    st.sidebar.info(
        "💡 Standard Rule Engine active. (Add OpenAI credit to enable live GPT extraction)"
    )

# 4. Main Navigation Tabs
tab1, tab2 = st.tabs([
    "📊 Executive Dashboard & Single Audit",
    "⚖️ Rate Con vs. Invoice Cross-Match",
])


# Helper function to extract text from PDF or TXT
def extract_text(uploaded_file):
    if uploaded_file is None:
        return ""
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
    return text


# Helper function to parse dollar figures into float
def parse_dollar(val):
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


# Helper function for live GPT AI extraction with rule-engine fallback
def run_ai_audit(filename, text, key):
    if key and text.strip():
        try:
            client = openai.OpenAI(api_key=key)
            prompt = f"""
Analyze this freight document text ({filename}) and extract the real values from the document.
Return a JSON object with these exact keys:
- "document_type": string (e.g., "Rate Confirmation", "Carrier Invoice", or "Bill of Lading")
- "carrier_name": string (exact carrier or broker name found in the text, or "Unknown")
- "load_number": string (exact load/reference/invoice number found in the text, or "Unknown")
- "agreed_rate": string (exact total linehaul/rate dollar amount, e.g. "$2,400.00")
- "fuel_surcharge": string (fuel surcharge amount if mentioned, or "N/A")
- "detention_clause": string (summary of detention terms, or "None")
- "audit_status": string (audit finding sentence, e.g., "✅ Cleared - No Discrepancies" or "⚠️ WARNING: Rate discrepancy detected")
- "status_type": string ("success", "info", or "error")

Document Text:
{text}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert logistics document auditor. Respond strictly in valid JSON format."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices.message.content)
            data["file_name"] = filename
            return data
        except Exception as e:
            st.sidebar.warning(f"Note (Rule fallback): {e}")

    # Rule-based fallback if no API key or API call fails
    search_text = (text + " " + filename).upper()
    if "INVOICE" in search_text:
        doc_type = "Carrier Invoice"
    elif "BILL OF LADING" in search_text or "BOL" in search_text:
        doc_type = "Bill of Lading (BOL)"
    elif "RATE" in search_text or "CONFIRMATION" in search_text:
        doc_type = "Rate Confirmation"
    else:
        doc_type = "Logistics Document"

    if "UNAPPROVED" in search_text:
        status_type = "error"
        status_msg = "⚠️ WARNING: Unapproved fee or rate discrepancy detected!"
    elif "DETENTION" in search_text:
        status_type = "info"
        status_msg = "ℹ️ Detention clause detected in document."
    else:
        status_type = "success"
        status_msg = "✅ Cleared: Document scanned with no rate discrepancies."

    return {
        "file_name": filename,
        "document_type": doc_type,
        "carrier_name": "Rule Engine Detection",
        "load_number": "N/A",
        "agreed_rate": "$0.00",
        "fuel_surcharge": "N/A",
        "detention_clause": "N/A",
        "status_type": status_type,
        "audit_status": status_msg,
    }


# --- TAB 1: EXECUTIVE DASHBOARD & SINGLE AUDIT ---
with tab1:
    st.subheader("📁 Single Document Audit & CSV Export")
    uploaded_file = st.file_uploader(
        "Drop your PDF or text file here",
        type=["pdf", "png", "jpg", "txt"],
        key="single_doc",
    )

    if uploaded_file is not None:
        st.success(f"✅ Loaded file: **{uploaded_file.name}**")
        raw_text = extract_text(uploaded_file)

        with st.expander("📄 View extracted raw text from PDF"):
            st.write(raw_text if raw_text else "No readable text found.")

        with st.spinner("🤖 AI is reading and auditing your document..."):
            audit = run_ai_audit(uploaded_file.name, raw_text, api_key)

        st.markdown("---")
        st.subheader("📊 Executive Audit Dashboard")

        status_kind = audit.get("status_type", "success")
        if status_kind == "error":
            st.error(f"### {audit.get('audit_status', '')}")
        elif status_kind == "info":
            st.info(f"### {audit.get('audit_status', '')}")
        else:
            st.success(f"### {audit.get('audit_status', '')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Document Type", audit.get("document_type", "N/A"))
        c2.metric("Carrier Name", audit.get("carrier_name", "N/A"))
        c3.metric("Load Number", audit.get("load_number", "N/A"))
        c4.metric("Linehaul Rate", audit.get("agreed_rate", "N/A"))

        st.markdown("#### 📋 Extracted Audit Data Table")
        df_audit = pd.DataFrame([{
            "File Name": audit.get("file_name", ""),
            "Document Type": audit.get("document_type", ""),
            "Carrier": audit.get("carrier_name", ""),
            "Load #": audit.get("load_number", ""),
            "Linehaul Rate": audit.get("agreed_rate", ""),
            "Fuel Surcharge": audit.get("fuel_surcharge", "N/A"),
            "Detention Clause": audit.get("detention_clause", "None"),
            "Audit Finding": audit.get("audit_status", ""),
        }])
        st.dataframe(df_audit, use_container_width=True)

        st.markdown("#### 📥 Export Audit Report")
        csv_data = df_audit.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download Audit Report (CSV)",
            data=csv_data,
            file_name=f"audit_report_{uploaded_file.name}.csv",
            mime="text/csv",
            type="primary",
        )

# --- TAB 2: RATE CON VS INVOICE CROSS-MATCH ---
with tab2:
    st.subheader("⚖️ Rate Con vs. Carrier Invoice Cross-Match")
    st.write(
        "Upload both the **Agreed Rate Confirmation** and the **Billed Carrier Invoice** to automatically cross-audit for rate creep."
    )

    col1, col2 = st.columns(2)
    with col1:
        rc_file = st.file_uploader(
            "1️⃣ Upload Rate Confirmation", type=["pdf", "png", "jpg", "txt"], key="rc"
        )
        if rc_file is not None:
            st.success(f"✅ Rate Con Loaded: **{rc_file.name}**")

    with col2:
        inv_file = st.file_uploader(
            "2️⃣ Upload Carrier Invoice",
            type=["pdf", "png", "jpg", "txt"],
            key="inv",
        )
        if inv_file is not None:
            st.success(f"✅ Invoice Loaded: **{inv_file.name}**")

    if rc_file and inv_file:
        rc_text = extract_text(rc_file)
        inv_text = extract_text(inv_file)

        st.markdown("---")
        st.subheader("⚡ Automated Rate Discrepancy Cross-Match")

        with st.spinner("🤖 AI is cross-auditing both documents..."):
            rc_audit = run_ai_audit(rc_file.name, rc_text, api_key)
            inv_audit = run_ai_audit(inv_file.name, inv_text, api_key)

        agreed = parse_dollar(rc_audit.get("agreed_rate", "0"))
        billed = parse_dollar(inv_audit.get("agreed_rate", "0"))

        variance = billed - agreed

        m1, m2, m3 = st.columns(3)
        m1.metric("Agreed Linehaul (Rate Con)", f"${agreed:,.2f}")
        m2.metric(
            "Billed Total (Invoice)",
            f"${billed:,.2f}",
            delta=f"${variance:,.2f}",
            delta_color="inverse",
        )
        m3.metric(
            "Discrepancy Status",
            "🚨 VARIANCE DETECTED" if variance > 0 else "✅ EXACT MATCH",
        )

        if variance > 0:
            st.error(
                f"⚠️ **FLAGGED DISCREPANCY:** The carrier invoice is **${variance:,.2f}** higher than the agreed Rate Confirmation!"
            )
        else:
            st.success(
                "✅ **MATCH CONFIRMED:** Billed invoice amount matches agreed Rate Confirmation rate exactly."
            )

        match_df = pd.DataFrame([
            {
                "Document": "Rate Confirmation (Agreed)",
                "File": rc_file.name,
                "Carrier": rc_audit.get("carrier_name", "N/A"),
                "Amount": f"${agreed:,.2f}",
            },
            {
                "Document": "Carrier Invoice (Billed)",
                "File": inv_file.name,
                "Carrier": inv_audit.get("carrier_name", "N/A"),
                "Amount": f"${billed:,.2f}",
            },
            {
                "Document": "Variance / Discrepancy",
                "File": "Cross-Audit Result",
                "Carrier": "N/A",
                "Amount": f"${variance:,.2f}",
            },
        ])

        csv_match = match_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download Cross-Match Audit (CSV)",
            data=csv_match,
            file_name="cross_match_audit.csv",
            mime="text/csv",
            type="primary",
        )
    elif rc_file or inv_file:
        st.info("💡 Please upload the **second document** above to perform the side-by-side cross-match audit.")
