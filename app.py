import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai 
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="LinkedIn Proposal Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- DATABASE SETUP ---
DB_FILE = "client_requests.db"

def init_db():
    """Initialize the SQLite database and create the requests table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            service_needed TEXT,
            client_headline TEXT,
            project_details TEXT,
            status TEXT,
            submitted_proposal TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_data() -> pd.DataFrame:
    """Load all records from the database into a pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM requests", conn)
    conn.close()
    return df

def add_request(name, service, headline, details):
    """Add a new client request to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO requests (client_name, service_needed, client_headline, project_details, status, submitted_proposal)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, service, headline, details, 'Pending', ''))
    conn.commit()
    conn.close()

def update_request(record_id, name, service, headline, details, status, proposal):
    """Update an existing record in the database by its ID."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE requests
        SET client_name = ?, service_needed = ?, client_headline = ?, project_details = ?, status = ?, submitted_proposal = ?
        WHERE id = ?
    ''', (name, service, headline, details, status, proposal, record_id))
    conn.commit()
    conn.close()

# Initialize the database on first run
init_db()

# --- API KEY MANAGEMENT ---
google_api_key = st.secrets["GOOGLE_API_KEY"]
if google_api_key:
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        st.error(f"Error configuring Google API: {e}")


# --- YOUR PROFILE/SERVICE DATA ---
# This data will be fed to the LLM to customize the proposal
MY_NAME = "Islam Khairy"
MY_HEADLINE = "Passionate Solopreneur | Mechanical BIM/VDC Engineer | Contech & Entrepreneurship Enthusiast | Career Development Coach & Startup Mentor"
MY_EXPERIENCE_SUMMARY = """
With 4+ years of experience mentoring over 1,500 trainees, I specialize in Career Coaching, 
Interview Preparation, Resume Writing, and Training. I have a proven track record of helping 
professionals refine their career paths, optimize their resumes to get past ATS, and confidently 
ace interviews. My unique background in Engineering Design also allows me to offer specialized 
mentorship to technical professionals.
"""
MY_SERVICES = {
    "Resume Writing": "I craft compelling, ATS-optimized resumes from scratch that highlight a client's key achievements and skills.",
    "Resume Review": "I analyze and provide detailed feedback to transform a resume into a powerful marketing document that gets noticed.",
    "Interview Preparation": "I conduct realistic mock interviews and provide actionable feedback to help clients walk into any interview with confidence and leave with an offer.",
    "Career Development Coaching": "I help clients gain clarity on their career goals and create a strategic roadmap for advancement.",
    "Training": "I offer customized training sessions on career-related topics.",
}

# --- SESSION STATE INITIALIZATION ---
# This keeps your data persistent as you interact with the app
if 'requests_df' not in st.session_state:
    st.session_state.requests_df = pd.DataFrame(columns=["Client Name", "Service Needed", "Client Headline", "Project Details", "Status", "Submitted Proposal"])
if 'generated_proposal' not in st.session_state:
    st.session_state.generated_proposal = ""


# --- LLM PROPOSAL GENERATION FUNCTION ---
def generate_proposal(client_name, service_needed, client_headline, project_details):
    if not google_api_key:
        st.error("Google API Key is missing. Please enter it above.")
        return None

    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are {MY_NAME}, a professional and empathetic Career Coach with the following headline: "{MY_HEADLINE}".
    Your experience is: {MY_EXPERIENCE_SUMMARY}
    Your available services are: {MY_SERVICES}

    A potential client, '{client_name}', has reached out for help.
    Their professional headline is: "{client_headline}".
    They are interested in the service: "{service_needed}".
    Here are the details of their request: "{project_details}".

    Based on all of this information, write a personalized, confident, and encouraging proposal to '{client_name}'.

    Follow this structure:
    1.  **Greeting:** Start with a warm, personalized greeting (e.g., "Hi {client_name},").
    2.  **Acknowledge and Validate:** Acknowledge their request and show you understand their situation based on their project details and headline. Connect their need to your expertise.
    3.  **Propose a Solution:** Briefly explain HOW you will help them using the specific service they requested ('{service_needed}'). Mention the tangible outcomes they can expect.
    4.  **Establish Credibility:** Subtly weave in your experience (e.g., "Having helped over 1,500 professionals...").
    5.  **Call to Action:** End with a clear next step. Suggest a brief, complimentary call to discuss their goals in more detail.

    IMPORTANT: The entire proposal must be concise and professional. Keep the total length under 1500 characters.
    """
    try:
        st.info("🤖 Generating proposal with Gemini... please wait.")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"An error occurred with the Google Gemini API: {e}")
        st.info("Common Error: If you see a 'permission denied' or 'API key not valid' error, please ensure you have enabled the 'Generative Language API' in your Google Cloud Project associated with the key.")
        return None

def enhance_proposal(proposal_text):
    if not google_api_key:
        st.error("Google API Key is missing. Please enter it above.")
        return proposal_text
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    Please review the following client proposal. Enhance it by making it more persuasive, confident, and concise. 
    Ensure it clearly communicates the value proposition and ends with a strong call to action.
    IMPORTANT: The final enhanced proposal must not exceed 1500 characters.

    Original Proposal:
    ---
    {proposal_text}
    ---
    """
    try:
        st.info("🤖 Enhancing proposal with Gemini...")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"An error occurred while enhancing: {e}")
        return proposal_text

# --- STREAMLIT APP LAYOUT ---

st.title("🚀 LinkedIn Service Proposal Assistant")
st.markdown("Streamline your client outreach by capturing requests and auto-generating personalized proposals.")


# Load data from the database
requests_df = load_data()


# --- COLUMNS FOR INPUT AND DISPLAY ---
col1, col2 = st.columns(2)

with col1:
    st.header("Step 1: Log a New Client Request")
    with st.form("new_request_form", clear_on_submit=True):
        client_name = st.text_input("Client Name")
        service_needed = st.selectbox("Service Needed", options=list(MY_SERVICES.keys()))
        client_headline = st.text_input("Client's LinkedIn Headline")
        project_details = st.text_area("Project Details (Copy-paste from LinkedIn)", height=150)
        submitted = st.form_submit_button("Add Request to Database")

        if submitted:
            if not all([client_name, service_needed, project_details]):
                st.warning("Please fill out all required fields.")
            else:
                add_request(client_name, service_needed, client_headline, project_details)
                st.success(f"Added request for {client_name}!")
                st.rerun()

with col2:
    st.header("Step 2: Generate & Refine Proposal")
    if not st.session_state.requests_df.empty:
        # Select a client from the pending requests
        pending_requests = requests_df[requests_df['status'] == 'Pending']
        if not pending_requests.empty:
            selected_client_name = st.selectbox(
                "Select a client to generate a proposal for:",
                options=pending_requests["Client Name"].tolist()
            )
            
            selected_row = pending_requests[pending_requests['display'] == selected_client_name].iloc[0]

            if 'proposal_text' not in st.session_state:
                st.session_state.proposal_text = ""

            if st.button(f"🤖 Generate Proposal for {selected_client_name}"):
                proposal = generate_proposal(
                    selected_row["Client Name"],
                    selected_row["Service Needed"],
                    selected_row["Client Headline"],
                    selected_row["Project Details"]
                )
                if proposal:
                    st.session_state.generated_proposal = proposal
        else:
            st.info("No pending requests to process.")
    else:
        st.info("Add a client request on the left to get started.")

    # Display the proposal in an editable text area
    edited_proposal = st.text_area("Your Generated Proposal", value=st.session_state.generated_proposal, height=300, key="proposal_editor")
    st.caption(f"Character count: {len(edited_proposal)}")

    # Buttons to act on the proposal
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✨ Enhance with LLM"):
            st.session_state.generated_proposal = enhance_proposal(edited_proposal)
            # This re-runs the script, so the editor will update with the new value.
            st.rerun()

    with c2:
        if st.button("📋 Copy to Clipboard"):
            st.success("Proposal copied! Now paste it into your LinkedIn message.")
            # The actual copy-to-clipboard is tricky in Streamlit, this is a user-friendly instruction
            # A component could be used for real copy functionality if needed.

    with c3:
        if st.button("✅ Mark as 'Contacted'"):
            if 'selected_client_name' in locals():
                update_request(
                    record_id=selected_row['id'],
                    name=selected_row['client_name'],
                    service=selected_row['service_needed'],
                    headline=selected_row['client_headline'],
                    details=selected_row['project_details'],
                    status='Contacted',
                    proposal=edited_proposal
                )
                st.session_state.generated_proposal = "" # Clear proposal
                st.success(f"Status for {selected_client_name} updated to 'Contacted'.")
                st.rerun()
            else:
                st.warning("Please select a pending client first.")


# --- DISPLAY THE REQUESTS TABLE ---
st.header("Client Request Dashboard")
if not st.session_state.requests_df.empty:
    st.dataframe(st.session_state.requests_df, use_container_width=True)
else:
    st.info("Your client requests will appear here once you add them.")


# --- NEW: EDITING SECTION ---
st.header("Edit an Existing Record")
with st.expander("Select a record to modify"):
    if not requests_df.empty:
        # We need a unique identifier for the selectbox key to avoid conflicts
        record_to_edit_id = st.selectbox(
            "Select Client Record",
            options=requests_df['id'],
            format_func=lambda x: f"ID: {x} - {requests_df.loc[requests_df['id'] == x, 'client_name'].iloc[0]}",
            key="editor_selectbox"
        )
        
        if record_to_edit_id:
            record_data = requests_df[requests_df['id'] == record_to_edit_id].iloc[0]

            with st.form("edit_form"):
                st.subheader(f"Editing Record for: {record_data['client_name']}")
                
                edit_name = st.text_input("Client Name", value=record_data['client_name'])
                edit_service = st.text_input("Service Needed", value=record_data['service_needed'])
                edit_headline = st.text_input("Client Headline", value=record_data['client_headline'])
                edit_details = st.text_area("Project Details", value=record_data['project_details'], height=100)
                edit_status = st.selectbox("Status", options=['Pending', 'Contacted', 'Follow-up', 'Closed'], index=['Pending', 'Contacted', 'Follow-up', 'Closed'].index(record_data['status']))
                edit_proposal = st.text_area("Submitted Proposal", value=record_data['submitted_proposal'], height=200)

                save_button = st.form_submit_button("Save Changes")
                if save_button:
                    update_request(
                        record_id=record_to_edit_id,
                        name=edit_name,
                        service=edit_service,
                        headline=edit_headline,
                        details=edit_details,
                        status=edit_status,
                        proposal=edit_proposal
                    )
                    st.success("Record updated successfully!")
                    st.rerun()
    else:
        st.info("No records to edit yet.")