# LinkedIn Service Proposal Assistant 🚀

This is a Streamlit application designed to streamline the process of responding to client requests on my LinkedIn Service Page.

## Features
-   Log new client requests from LinkedIn.
-   Store client data in a clean, viewable table.
-   Utilize Google's Gemini Pro AI to automatically generate personalized, professional proposals.
-   Enhance, edit, and save the final proposal sent to the client.

## Setup and Run

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and activate a virtual environment** (e.g., using conda):
    ```bash
    conda create --name proposal_app python=3.9
    conda activate proposal_app
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
    You will be prompted to enter your Google AI Studio API key in the web interface.