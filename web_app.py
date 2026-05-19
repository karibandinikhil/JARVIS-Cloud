import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from gtts import gTTS
import io
import base64
import PyPDF2 
import docx 
from pptx import Presentation 

# --- 1. SECURITY & CONNECTION ---
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("Security Alert: API Key not found. Please check your .env file.")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1", 
    api_key=api_key 
)

# --- 2. UI SETUP ---
st.set_page_config(page_title="J.A.R.V.I.S. Cloud", page_icon="🌐", layout="centered")
st.title("J.A.R.V.I.S. Cloud Interface")
st.caption("Secure Cloud Connection Established. Omni-Document Analyst Online.")

# --- 3. MEMORY SYSTEM (UPGRADED FOR MASSIVE DETAIL) ---
memory_file = "jarvis_memory.json"

def load_memory():
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as file:
            return json.load(file)
    system_prompt = (
        "You are J.A.R.V.I.S., a highly advanced AI assistant. "
        "You are currently operating in a secure cloud web environment. "
        "Address me as Sir. NEVER use asterisks or lists. "
        "CRITICAL DIRECTIVE: When asked to explain something, provide extremely detailed, comprehensive, and exhaustive long-form answers. Do not summarize unless explicitly asked. Provide maximum depth. "
        "When provided with document text, read it carefully and answer questions based ONLY on that text."
    )
    return [{"role": "system", "content": system_prompt}]

def save_memory(chat_history):
    with open(memory_file, 'w') as file:
        json.dump(chat_history, file, indent=4)

if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

# --- 4. DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- 5. THE AI ENGINES ---
def speak_out_loud(text):
    tts = gTTS(text=text, lang='en', tld='co.uk')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

# THE CHAT ENGINE (UNLOCKED TOKENS)
def process_command(user_text):
    with st.chat_message("user"):
        st.write(user_text)
        
    st.session_state.messages.append({"role": "user", "content": user_text})
    smart_memory = [st.session_state.messages[0]] + st.session_state.messages[-25:]
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*(Processing...)*")
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=smart_memory, 
                temperature=0.7,
                max_tokens=4000, # <-- UNLOCKED: Allows massive essays
            )
            answer = completion.choices[0].message.content
            message_placeholder.write(answer)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_memory(st.session_state.messages)
            speak_out_loud(answer)
        except Exception as e:
            message_placeholder.error(f"System Error: {e}")

def process_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    with st.chat_message("user"):
        st.write("[Image Provided]")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*(Analyzing Image...)*")
        try:
            vision_messages = [
                {"role": "system", "content": "You are J.A.R.V.I.S. Describe the image briefly."},
                {"role": "user", "content": [
                    {"type": "text", "text": "What do you see?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct", 
                messages=vision_messages, 
                temperature=0.7,
            )
            answer = completion.choices[0].message.content
            message_placeholder.write(answer)
            st.session_state.messages.append({"role": "user", "content": "[I showed you an image]"})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_memory(st.session_state.messages)
            speak_out_loud(answer)
        except Exception as e:
            message_placeholder.error(f"Vision Error: {e}")

# THE OMNI-DOCUMENT ENGINE (UNLOCKED TOKENS)
def process_document(file):
    with st.chat_message("user"):
        st.write(f"[Uploaded Document: {file.name}]")
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*(Reading document...)*")
        
        extracted_text = ""
        file_extension = file.name.split('.')[-1].lower()
        
        try:
            if file_extension == 'txt':
                extracted_text = file.getvalue().decode("utf-8")
            elif file_extension == 'pdf':
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
            elif file_extension == 'docx':
                doc = docx.Document(file)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
            elif file_extension == 'pptx':
                ppt = Presentation(file)
                for slide in ppt.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            extracted_text += shape.text + "\n"
            
            if len(extracted_text) > 20000:
                extracted_text = extracted_text[:20000] + "... [Document truncated due to AI memory limits.]"
            
            system_injection = f"I have uploaded a document named {file.name}. Here is the text inside it:\n\n{extracted_text}\n\nAcknowledge that you have read it and provide a highly detailed summary of its contents."
            
            st.session_state.messages.append({"role": "user", "content": system_injection})
            smart_memory = [st.session_state.messages[0]] + st.session_state.messages[-25:]
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=smart_memory, 
                temperature=0.7,
                max_tokens=4000, # <-- UNLOCKED: Allows massive document summaries
            )
            answer = completion.choices[0].message.content
            message_placeholder.write(answer)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_memory(st.session_state.messages)
            speak_out_loud(answer)
            
        except Exception as e:
            message_placeholder.error(f"Document Reading Error: {e}")

# ==========================================
# --- 6. THE CONTROL DECK (UI) ---
# ==========================================
st.write("---")

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 4])

with c1:
    with st.popover("🖼️ Pic"):
        uploaded_img = st.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])
        if uploaded_img:
            process_image(uploaded_img.getvalue())

with c2:
    with st.popover("📄 Doc"):
        uploaded_doc = st.file_uploader("Upload File", type=['pdf', 'txt', 'docx', 'pptx'])
        if uploaded_doc:
            process_document(uploaded_doc)

with c3:
    with st.popover("📷 Cam"):
        camera_photo = st.camera_input("Take Photo")
        if camera_photo:
            process_image(camera_photo.getvalue())

with c4:
    with st.popover("🎙️ Mic"):
        audio_value = st.audio_input("Speak Command")
        if audio_value:
            st.toast("Processing audio...", icon="🎙️")
            try:
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", audio_value.read()),
                    model="whisper-large-v3"
                )
                process_command(transcription.text)
            except Exception as e:
                st.error(f"Audio Error: {e}")

if text_input := st.chat_input("Type Command, Sir..."):
    process_command(text_input)