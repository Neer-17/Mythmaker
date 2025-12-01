import streamlit as st
import os
import asyncio
import logging
import nest_asyncio
import json
from dotenv import load_dotenv
from PIL import Image

# Standard GenAI Library
from google import genai
from google.genai import types

# Keep ADK structure for Definitions
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

# 1. SETUP
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Mythmaker_Runner")

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Missing GOOGLE_API_KEY in .env")
    st.stop()

# Initialize the Standard Client
client = genai.Client(api_key=api_key)

# 2. DEFINE AGENTS (Blueprints)

# Visionary: Sees the image
visionary_agent = LlmAgent(
    model=Gemini(model_name="gemini-2.5-pro", api_key=api_key),
    name="Visionary",
    instruction="You are The Visionary. Analyze images and list 3 specific, vivid visual details that look spooky or mysterious."
)

# Investigator: Searches REAL history
investigator_agent = LlmAgent(
    model=Gemini(model_name="gemini-2.5-pro", api_key=api_key),
    name="Investigator",
    instruction=(
        "You are The Investigator. You MUST use Google Search to find verified historical facts. "
        "Focus on: dark history, crimes, local legends, and specific dates. "
        "Do NOT make up facts. If you can't find info, state that."
    )
)

# Bard: Writes the story
mythmaker_agent = LlmAgent(
    model=Gemini(model_name="gemini-2.5-pro", api_key=api_key),
    name="Bard",
    instruction="You are The Local Mythmaker. Write a short 'Micro-Myth' (max 120 words) weaving verified history into a spooky narrative and first person to the user."
)

# Critic: Evaluates quality
critic_agent = LlmAgent(
    model=Gemini(model_name="gemini-2.5-pro", api_key=api_key),
    name="Critic",
    instruction=(
        "You are the Editor. Evaluate the myth for spookiness and historical accuracy integration. "
        "Return ONLY a JSON object: {'score': int (1-10), 'feedback': 'string'}. "
        "Do not output markdown."
    )
)

# 3. ORCHESTRATION & RUNNER

async def run_pipeline(image_bytes, mime_type, location):
    session_memory = {
        "visuals": "",
        "lore": "",
        "drafts": [],
        "final_myth": ""
    }

    # --- UNIVERSAL RUNNER (With Real Tools) ---
    def execute_agent(agent, prompt, image_input=None, use_google_search=False):
        logger.info(f"⚡ Executing {agent.name}...")
        
        # 1. Config System Instruction
        config = types.GenerateContentConfig(
            system_instruction=agent.instruction,
            temperature=0.7
        )
        
        # 2. Enable Real Google Search if requested
        if use_google_search:
            # This enables the built-in Gemini Search Tool
            config.tools = [types.Tool(google_search=types.GoogleSearch())]
            config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=False)

        # 3. Prepare Content
        content = []
        if image_input:
            content.append(types.Part.from_bytes(data=image_input, mime_type=mime_type))
        content.append(prompt)

        # 4. Execute via Standard Client
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=content,
                config=config
            )
            
            # Extract text carefully (Grounding metadata can sometimes split parts)
            full_text = ""
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        full_text += part.text
            return full_text if full_text else "No response generated."

        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            return f"Error: {str(e)}"

    # --- PHASE 1: PARALLEL GATHERING ---
    logger.info("--- Phase 1: Parallel ---")
    
    # Task A: Vision
    vision_task = asyncio.to_thread(
        execute_agent, 
        visionary_agent, 
        "Describe the atmosphere.", 
        image_input=image_bytes
    )
    
    # Task B: Investigation (NOW WITH REAL SEARCH)
    investigator_task = asyncio.to_thread(
        execute_agent,
        investigator_agent,
        f"Find specific dark history and ghost stories for: {location}",
        use_google_search=True 
    )
    
    visuals, lore = await asyncio.gather(vision_task, investigator_task)
    
    session_memory["visuals"] = visuals
    session_memory["lore"] = lore

    # --- PHASE 2: CONTEXT COMPACTION ---
    context_package = (
        f"LOCATION: {location}\n"
        f"VISUALS: {visuals}\n"
        f"VERIFIED LORE: {lore}\n"
    )

    # --- PHASE 3: LOOP & EVALUATION ---
    logger.info("--- Phase 3: Loop ---")
    
    current_draft = ""
    feedback = ""
    
    for i in range(2): 
        # 3a. Generate
        prompt_text = "Write the myth."
        if feedback:
            prompt_text = f"Refine this myth based on feedback: {feedback}"
            
        full_prompt = f"{prompt_text}\n\nCONTEXT:\n{context_package}"
        
        current_draft = await asyncio.to_thread(
            execute_agent, mythmaker_agent, full_prompt
        )
        session_memory["drafts"].append(current_draft)

        # 3b. Critic Evaluate
        eval_result = await asyncio.to_thread(
            execute_agent, critic_agent, f"Evaluate:\n{current_draft}"
        )
        
        try:
            clean_json = eval_result.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            score = data.get("score", 0)
            feedback = data.get("feedback", "Good.")
            
            if score >= 8:
                break
        except:
            break

    session_memory["final_myth"] = current_draft
    return session_memory

# 4. UI
st.set_page_config(page_title="Mythmaker", layout="wide")

st.title("The Local Mythmaker")

col1, col2 = st.columns([1, 1])
with col1:
    location_input = st.text_input("Enter Location", "Tower of London")
with col2:
    uploaded_file = st.file_uploader("Upload Artifact", type=["jpg", "png", "jpeg"])

if st.button("Summon Agents"):
    if uploaded_file and location_input:
        image_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        display_image = Image.open(uploaded_file)
        
        with st.status("🔮 Agents are communing...", expanded=True) as status:
            try:
                memory = asyncio.run(run_pipeline(image_bytes, mime_type, location_input))
                
                st.session_state.memory = memory
                st.session_state.analysis_complete = True
                st.session_state.current_image = display_image
                
                status.update(label="Myth Manifested!", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Error: {e}")
                logger.exception("Trace:")

if "analysis_complete" in st.session_state and st.session_state.analysis_complete:
    st.divider()
    mem = st.session_state.memory
    
    c1, c2 = st.columns([2, 3])
    with c1:
        st.image(st.session_state.current_image, caption="Analyzed Artifact", use_container_width=True)
    with c2:
        st.subheader(f"The Myth of {location_input}")
        # Apply the custom CSS class
        st.markdown(f'<div class="myth-box">{mem.get("final_myth")}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Observability Panel
    with st.expander("🔍 Investigator's Notes (Real Data)", expanded=False):
        st.markdown("### 🕸️ Visual Analysis")
        st.write(mem.get('visuals'))
        st.markdown("### 📜 Verified History")
        st.info(mem.get('lore')) 
        st.markdown("### 🔄 Iteration Log")
        for idx, draft in enumerate(mem.get('drafts', [])):
            st.text(f"Draft {idx+1}: {draft[:100]}...")