# AI-Powered Creative Story Generator (ARI3333)

This project implements a Streamlit-based creative story generation system powered by the LLaMA 3.2-3B-Instruct model via the Hugging Face Inference API. It was developed as part of the **ARI3333: Generative AI** module and focuses on applying prompt engineering and user-driven interaction for personalized content creation.

## Project Summary

The system allows users to:
- Select genre, tone, character, setting, and word length
- Generate full-length stories with clear structure and plot
- Refine stories by changing tone, character, or applying custom instructions
- Export finalized versions as PDF documents

All model interaction occurs via API calls to Hugging Face's hosted inference endpoint.

---

## Code Explanation

### 1. Streamlit Interface & Session Management

The user interface is built entirely with Streamlit. The sidebar collects input parameters (`genre`, `tone`, `character`, `setting`, and `word_limit`), while the main panel displays the current story and editing options.

Session state variables (`st.session_state`) are used to store:
- The current story (`current_story`)
- The selected parameters (`story_params`)
- Intermediate refined versions (`temp_refined_story`)

---

### 2. Prompt Construction

Prompts are programmatically generated to guide the language model toward producing complete, coherent stories. The prompt format includes genre, tone, and story constraints (word length, structure).

Example:

**Write a complete {genre} story with a {tone} tone about {character} in {setting}. The story must be between {min_words} and {max_words} words. Include a clear beginning, middle, and end with proper character development and plot progression. Write the story directly without any explanations or meta-commentary.**



Word length presets include:
- Really short (150–300 words)
- Short (400–600)
- Medium (700–900)
- Long (1000–1200)
- Very long (1300–1500)

---

### 3. Story Generation

The `generate_story()` function handles model communication:
- Sends POST requests to the LLaMA 3.2-3B-Instruct endpoint
- Applies decoding strategies (`temperature`, `top_p`, `do_sample`)
- Cleans received text using heuristics to remove undesired system responses

If generation fails, detailed error handling and debugging info are displayed in the UI.

---

### 4. Refinement Tools

Users can modify the story in three ways:
- **Change Tone**: Reuses the same parameters with a new tone
- **Modify Character**: Keeps tone/setting but changes the main character
- **Custom Instruction**: Appends user-defined changes to regenerate a tailored version

Each refinement results in a new API call with an updated prompt and story content.

Users can preview refined versions and choose to "keep this version" to update their session.

---

### 5. PDF Export

The `export_to_pdf()` function creates downloadable PDF files containing:
- Title
- Genre and tone headers
- Formatted story text using FPDF with encoding fixes

The final document is offered via a Streamlit download button and deleted after use.

---

## Summary of Report Findings

The accompanying report highlights key implementation choices, model behavior, and ethical considerations:

- **Prompt Engineering**: Precise prompt structuring plays a crucial role in narrative quality. Word constraints and explicit structure guidance improve output consistency.
- **Interactivity**: Giving users control over tone, character, and plot enhances engagement and personalization.
- **Model Behavior**: The LLaMA model generally produces coherent and relevant stories but may occasionally inject meta-comments or repeat content, which the cleaning function mitigates.
- **Limitations**:
  - Tone and character drift in longer generations
  - Lack of model-side memory (each request is stateless)
  - No fine-tuning; all output relies on zero-shot prompting
- **Ethics**:
  - Prompts are kept neutral to avoid bias
  - User-generated content is fully transparent and editable
  - No toxic or harmful prompt content is allowed

---

## Conclusion

This assignment demonstrates the application of large language models in creative storytelling with real-time user interaction and structured prompt control. The integration of Streamlit for UI and the Hugging Face API for backend generation creates an accessible and flexible tool for exploring generative narrative capabilities.

The project reflects the intersection of NLP, prompt design, and user-centered AI applications within the context of Generative AI.
