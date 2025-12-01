# 🧛 Mythmaker: AI-Powered Folklore Generator

**Mythmaker** is a multi-agent AI application that weaves verified historical facts into spooky, atmospheric "micro-myths" based on user-uploaded images. 

Powered by **Google Gemini 2.5 Pro**, this system utilizes a team of four specialized AI agents to analyze visual cues, perform real-time Google searches for historical grounding, and iteratively refine narratives using an automated feedback loop.

## 🚀 Key Features

* **Multi-Agent Architecture:** Orchestrates four distinct personas (Visionary, Investigator, Bard, Critic).
* **Multimodal Analysis:** "Visionary" agent analyzes uploaded images for atmospheric and visual details.
* **Real-Time Grounding:** "Investigator" agent utilizes 
**Google Search** to fetch verified historical data, ensuring myths are rooted in reality.
* **Automated Quality Control:** "Critic" agent evaluates drafts and enforces a feedback loop, rejecting low-quality stories and requesting rewrites automatically.
* **Observability:** Built-in tracing allowing users to see the raw "thought process" and search results of every agent.

## 🛠️ Tech Stack

* **Engine:** Python 3.10+
* **AI Model:** Google Gemini 2.5 Pro (`gemini-2.5-pro`)
* **SDK:** Google Gen AI SDK (`google-genai`)
* **Interface:** Streamlit
* **Orchestration:** `asyncio` for parallel execution

## 🏗️ Architecture

The system follows a **Map-Reduce-Refine** pattern:



[Image of multi-agent system architecture diagram]


1.  **Phase 1 (Parallel Gathering):** * *Visionary Agent* extracts visual cues from the image.
    * *Investigator Agent* performs tool calls (Google Search) to find local lore.
2.  **Phase 2 (Synthesis):**
    * Context compaction merges visual data and historical facts into a single prompt package.
3.  **Phase 3 (The Loop):**
    * *Bard Agent* drafts the myth.
    * *Critic Agent* scores the myth (1-10).
    * *Logic:* If the score is < 8, the draft and feedback are fed back to the Bard for a rewrite (Max 2 retries).

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Neer-17/Mythmaker.git
    cd mythmaker
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables**
    Create a `.env` file in the root directory and add your Google Cloud API key:
    ```env
    GOOGLE_API_KEY=your_actual_api_key_here
    ```
    *(Note: Ensure your API key has access to Gemini 2.0 Flash Experimental)*

## 🔮 Usage

1.  Run the application:
    ```bash
    streamlit run app.py
    ```
2.  Open your browser to the local URL (usually `http://localhost:8501`).
3.  **Input:** Enter a location (e.g., "Tower of London") and upload an image (e.g., an old castle photo).
4.  **Click "Summon Agents":** Watch the logs as the agents perform research and writing in real-time.

## 📂 Project Structure
├── app.py # Main application logic & agent definitions ├── requirements.txt # Python dependencies ├── .env # API keys (not committed to git) └── README.md # Documentation
