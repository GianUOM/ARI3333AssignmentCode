import streamlit as st
from huggingface_hub import InferenceClient
from fpdf import FPDF
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import requests
import traceback
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not API_KEY:
    st.error("API Key not found. Please set HUGGINGFACE_API_KEY in your .env file.")
    st.stop()

# Initialize session state for the story
if "current_story" not in st.session_state:
    st.session_state["current_story"] = ""

# Store original parameters in session state
if "story_params" not in st.session_state:
    st.session_state.story_params = {
        "genre": "",
        "tone": "",
        "word_limit": "",
        "character": "",
        "setting": ""
    }

def clean_generated_text(response_text, prompt):
    """Cleans the generated text by removing prompts and explanations."""
    if response_text.startswith(prompt):
        response_text = response_text[len(prompt):].strip()
    
    patterns_to_remove = [
        "In this rewritten version",
        "The emotional tone of the rewritten story",
        "While keeping the main plot and setting",
        "Here's the story with a",
        "I'd like to rewrite this story with a",
        "Here's your story with a",
        "The changes made include:",
        "Overall, the rewritten story",
        "**Act I:",
        "**Act II:",
        "**Act III:",
        "**Act IV:",
        "---",
        "**Characters:**",
        "**Setting:**"
    ]
    
    end_positions = []
    for pattern in patterns_to_remove:
        pos = response_text.find(pattern)
        if pos != -1:
            end_positions.append(pos)
    
    if end_positions:
        response_text = response_text[:min(end_positions)].strip()
    
    if "**" in response_text:
        response_text = response_text.split("**")[0].strip()
    
    response_text = response_text.replace("**", "")
    
    if "tone:" in response_text.lower():
        response_text = response_text.split("tone:")[-1].strip()
    
    return response_text.strip()

def generate_story(api_key, prompt, max_tokens):
    """Generate story with better error handling and feedback."""
    try:
        API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "x-wait-for-model": "true"
        }
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.8,
                "top_p": 0.9,
                "do_sample": True
            }
        }

        with st.spinner("Generating story..."):
            st.info("Sending request to API...")
            response = requests.post(API_URL, headers=headers, json=data)
            
            if response.status_code != 200:
                st.error(f"API Error: Status Code {response.status_code}")
                st.error(f"Error Details: {response.text}")
                return None

            response_data = response.json()
            st.info("Received response from API")
            
            if isinstance(response_data, list) and len(response_data) > 0:
                generated_text = response_data[0].get("generated_text", "")
                if not generated_text:
                    st.error("No text was generated")
                    return None
                cleaned_text = clean_generated_text(generated_text, prompt)
                if not cleaned_text:
                    st.error("Text was cleaned but resulted in empty content")
                    return None
                return cleaned_text
            else:
                st.error(f"Unexpected API response format: {response_data}")
                return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error generating story: {str(e)}")
        st.error(f"Error type: {type(e)}")
        return None

def export_to_pdf(story, genre, tone):
    """Exports the story to a PDF file."""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Generated Story", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Genre: {genre}", ln=True)
        pdf.cell(0, 10, f"Tone: {tone}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", size=12)
        paragraphs = story.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                pdf.multi_cell(0, 10, paragraph.encode('latin-1', 'replace').decode('latin-1'))
                pdf.ln(5)

        file_name = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(file_name)
        return file_name
    except Exception as e:
        st.error(f"Failed to export story to PDF: {str(e)}")
        return None

def create_prompt(genre, tone, character, setting, word_limit):
    """Creates a story prompt based on user input."""
    word_limits = {
        "Really short (150 - 300 words)": (150, 300),
        "Short (400 - 600 words)": (400, 600),
        "Medium (700 - 900 words)": (700, 900),
        "Long (1000 - 1200 words)": (1000, 1200),
        "Very long (1300 - 1500 words)": (1300, 1500)
    }
    min_words, max_words = word_limits[word_limit]
    return (
        f"Write a complete {genre} story with a {tone} tone about {character} in {setting}. "
        f"The story must be between {min_words} and {max_words} words. "
        "Include a clear beginning, middle, and end with proper character development and plot progression. "
        "Write the story directly without any explanations or meta-commentary. "
    )

def handle_keep_version(refined_story):
    """Helper function to handle keeping a new version of the story"""
    try:
        if not refined_story:
            st.error("No refined story to save")
            return False
            
        # Debug info
        st.write("Debug - Original story:", st.session_state["current_story"][:100])
        st.write("Debug - New story:", refined_story[:100])
        
        # Update the story in session state
        st.session_state["current_story"] = refined_story
        
        # Update story parameters if necessary
        if "story_params" in st.session_state:
            st.session_state.story_params["last_modified"] = datetime.now().isoformat()
        
        return True
        
    except Exception as e:
        st.error(f"Error saving new version: {str(e)}")
        return False

# Word limits dictionary
word_limits = {
    "Really short (150 - 300 words)": (150, 300),
    "Short (400 - 600 words)": (400, 600),
    "Medium (700 - 900 words)": (700, 900),
    "Long (1000 - 1200 words)": (1000, 1200),
    "Very long (1300 - 1500 words)": (1300, 1500)
}

# Streamlit UI setup
st.title("Creative Story Generator")
st.sidebar.header("Story Parameters")

# User input fields
genre = st.sidebar.selectbox("Genre:", [
    "Science Fiction", "Fantasy", "Horror", "Mystery", "Romance", "Adventure", 
    "Historical Fiction", "Thriller", "Drama", "Comedy", "Action"
])

tone = st.sidebar.selectbox("Tone:", [
    "Adventurous", "Emotional", "Humorous", "Dark", "Mysterious", "Romantic", "Philosophical"
])

character = st.sidebar.text_input("Character:")
setting = st.sidebar.text_input("Setting:")
word_limit = st.sidebar.selectbox("Word Limit:", list(word_limits.keys()))

# Generate Story button
if st.sidebar.button("Generate Story"):
    if not character.strip() or not setting.strip():
        st.warning("Please provide both a character and a setting.")
    else:
        st.session_state.story_params = {
            "genre": genre,
            "tone": tone,
            "word_limit": word_limit,
            "character": character,
            "setting": setting
        }
        prompt = create_prompt(genre, tone, character, setting, word_limit)
        max_tokens = word_limits[word_limit][1] * 2
        story = generate_story(API_KEY, prompt, max_tokens)

        if story:
            st.session_state["current_story"] = story
            st.success("Story generated successfully!")

# Display the current story and refinement options
if st.session_state["current_story"]:
    st.markdown("### Generated Story:")
    story_area = st.text_area("Current Story:", st.session_state["current_story"], height=300)

    # Refinement options section
with st.expander("Refine Story"):
    refine_option = st.radio(
        "What would you like to change?",
        ["Change Tone", "Modify Character", "Other Custom Change"]
    )

    # Option 1: Change Tone
    if refine_option == "Change Tone":
        new_tone = st.selectbox(
            "Select new tone:",
            ["Adventurous", "Emotional", "Humorous", "Dark", "Mysterious", "Romantic", "Philosophical"],
            key="tone_select"
        )
        
        if st.button("Apply Tone Change", key="apply_tone"):
            try:
                current_word_limit = st.session_state.story_params['word_limit']
                min_words, max_words = word_limits[current_word_limit]
                max_tokens = max_words * 2
                
                refine_prompt = create_prompt(
                    st.session_state.story_params['genre'],
                    new_tone,
                    st.session_state.story_params['character'],
                    st.session_state.story_params['setting'],
                    current_word_limit
                )
                
                with st.spinner("Refining story..."):
                    refined_story = generate_story(API_KEY, refine_prompt, max_tokens)
                    
                    if refined_story:
                        # Store the refined story in session state
                        st.session_state['temp_refined_story'] = refined_story
                        
                        # Display the refined story
                        st.markdown("### Refined Story:")
                        st.text_area(
                            "Preview", 
                            st.session_state['temp_refined_story'],
                            height=300, 
                            key=f"refined_story_preview_{int(time.time())}"
                        )
                        
                        # Keep version button
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Keep This Version", key=f"keep_version_{int(time.time())}"):
                                if handle_keep_version(st.session_state['temp_refined_story']):
                                    # Update the tone in story parameters
                                    st.session_state.story_params['tone'] = new_tone
                                    st.success("New version saved!")
                                    time.sleep(0.5)
                                    st.rerun()
                    else:
                        st.error("Failed to generate refined story. Please try again.")
                        
            except Exception as e:
                st.error(f"Error during tone refinement: {str(e)}")
                st.error(traceback.format_exc())

    # Option 2: Modify Character
    elif refine_option == "Modify Character":
        new_character = st.text_input(
            "Describe the new main character:",
            key="char_input"
        )
        
        if st.button("Apply Character Change", key="apply_char"):
            try:
                current_word_limit = st.session_state.story_params['word_limit']
                min_words, max_words = word_limits[current_word_limit]
                max_tokens = max_words * 2
                
                refine_prompt = create_prompt(
                    st.session_state.story_params['genre'],
                    st.session_state.story_params['tone'],
                    new_character,
                    st.session_state.story_params['setting'],
                    current_word_limit
                )
                
                with st.spinner("Refining story..."):
                    refined_story = generate_story(API_KEY, refine_prompt, max_tokens)
                    
                    if refined_story:
                        # Store the refined story in session state
                        st.session_state['temp_refined_story'] = refined_story
                        
                        # Display the refined story
                        st.markdown("### Refined Story:")
                        st.text_area(
                            "Preview", 
                            st.session_state['temp_refined_story'],
                            height=300, 
                            key=f"refined_story_preview_{int(time.time())}"
                        )
                        
                        # Keep version button
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Keep This Version", key=f"keep_version_{int(time.time())}"):
                                if handle_keep_version(st.session_state['temp_refined_story']):
                                    # Update the character in story parameters
                                    st.session_state.story_params['character'] = new_character
                                    st.success("New version saved!")
                                    time.sleep(0.5)
                                    st.rerun()
                    else:
                        st.error("Failed to generate refined story. Please try again.")
                        
            except Exception as e:
                st.error(f"Error during character refinement: {str(e)}")
                st.error(traceback.format_exc())

    # Option 3: Custom Change
    else:
        custom_instruction = st.text_area(
            "Describe what changes you'd like to make to the story:",
            placeholder="Example: Make the ending more surprising, or add more dialogue...",
            key="custom_input"
        )
        
        if st.button("Apply Custom Change", key="apply_custom"):
            try:
                current_word_limit = st.session_state.story_params['word_limit']
                min_words, max_words = word_limits[current_word_limit]
                max_tokens = max_words * 2
                
                refine_prompt = (
                    f"Here is a {st.session_state.story_params['genre']} story with a "
                    f"{st.session_state.story_params['tone']} tone about "
                    f"{st.session_state.story_params['character']} in "
                    f"{st.session_state.story_params['setting']}:\n\n"
                    f"{story_area}\n\n"
                    f"Rewrite this story with the following change: {custom_instruction}. "
                    f"The story must be between {min_words} and {max_words} words. "
                    "Keep the same genre, tone, character, and setting, but incorporate the requested change. "
                    "Write the story directly without any explanations or meta-commentary."
                )
                
                with st.spinner("Refining story..."):
                    refined_story = generate_story(API_KEY, refine_prompt, max_tokens)
                    
                    if refined_story:
                        # Store the refined story in session state
                        st.session_state['temp_refined_story'] = refined_story
                        
                        # Display the refined story
                        st.markdown("### Refined Story:")
                        st.text_area(
                            "Preview", 
                            st.session_state['temp_refined_story'],
                            height=300, 
                            key=f"refined_story_preview_{int(time.time())}"
                        )
                        
                        # Keep version button
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Keep This Version", key=f"keep_version_{int(time.time())}"):
                                if handle_keep_version(st.session_state['temp_refined_story']):
                                    # Add custom change to story parameters for tracking
                                    st.session_state.story_params['last_custom_change'] = custom_instruction
                                    st.success("New version saved!")
                                    time.sleep(0.5)
                                    st.rerun()
                    else:
                        st.error("Failed to generate refined story. Please try again.")
                        
            except Exception as e:
                st.error(f"Error during custom refinement: {str(e)}")
                st.error(traceback.format_exc())


    # PDF export button
    if st.button("Export Story to PDF"):
        with st.spinner("Creating PDF..."):
            pdf_file = export_to_pdf(st.session_state["current_story"], genre, tone)
            if pdf_file:
                try:
                    with open(pdf_file, "rb") as file:
                        pdf_bytes = file.read()
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )
                    os.remove(pdf_file)
                except Exception as e:
                    st.error(f"Error preparing download: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.info("Built with Streamlit and Hugging Face API.")
