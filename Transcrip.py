import streamlit as st
import moviepy.editor as mp
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
import time
from fpdf import FPDF

# Set the path to ffmpeg if required
# AudioSegment.converter = r"/path/to/ffmpeg"  # Change this if needed

def extract_audio(video_path):
    video = mp.VideoFileClip(video_path)
    audio_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    video.audio.write_audiofile(audio_file_path)
    video.close()  # Ensure the video file is closed
    return audio_file_path

def convert_audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_path)
    temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    
    chunk_duration_ms = 5000  # 5 seconds
    total_duration_ms = len(audio)
    chunks = (total_duration_ms // chunk_duration_ms) + (1 if total_duration_ms % chunk_duration_ms != 0 else 0)
    text = ""
    
    start_time = time.time()
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    for i in range(chunks):
        chunk_start = i * chunk_duration_ms
        chunk_end = min(chunk_start + chunk_duration_ms, total_duration_ms)
        audio_chunk = audio[chunk_start:chunk_end]
        audio_chunk.export(temp_audio_path, format="wav")
        
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
        
        try:
            chunk_text = recognizer.recognize_google(audio_data)
            text += chunk_text + " "
        except sr.UnknownValueError:
            text += "[Unintelligible] "
        except sr.RequestError as e:
            text += f"[Error: {e}] "
        
        # Update the progress
        progress_percentage = int(((i + 1) / chunks) * 100)
        elapsed_time = time.time() - start_time
        estimated_total_time = (elapsed_time / (i + 1)) * chunks
        estimated_time_remaining = estimated_total_time - elapsed_time
        
        progress_bar.progress(progress_percentage)
        progress_text.text(f"Transcription Progress: {progress_percentage}% - Estimated Time Remaining: {int(estimated_time_remaining)} seconds")
    
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
    
    return text

def save_text_to_pdf(text, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(pdf_path)

# Streamlit UI
st.title("Video and Audio Transcription - SBA Info Solutions")

# Tab for video transcription
st.header("Video to Text Transcription")
uploaded_video_file = st.file_uploader("Upload a video file", type=["mp4"], key="video")
if uploaded_video_file:
    with st.spinner('Extracting audio and converting to text...'):
        video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        with open(video_path, "wb") as f:
            f.write(uploaded_video_file.getbuffer())
        
        audio_path = extract_audio(video_path)
        result_text = convert_audio_to_text(audio_path)
        
        st.subheader("Transcription Text")
        st.text_area("Transcription", result_text, height=300)
        
        # Generate unique filenames for the downloads
        timestamp = int(time.time())
        pdf_path = f"transcription_{timestamp}.pdf"
        save_text_to_pdf(result_text, pdf_path)
        
        st.download_button(
            label="Download Transcription as PDF",
            data=open(pdf_path, "rb").read(),
            file_name=pdf_path,
            mime="application/pdf"
        )
        
        # Remove temporary files
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(pdf_path)
        
        st.success("Audio extracted and converted to text successfully!")

# Tab for audio transcription
st.header("Audio to Text Transcription")
uploaded_audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"], key="audio")
if uploaded_audio_file:
    with st.spinner('Converting audio to text...'):
        audio_format = uploaded_audio_file.name.split('.')[-1]
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}").name
        with open(audio_path, "wb") as f:
            f.write(uploaded_audio_file.getbuffer())
        
        result_text = convert_audio_to_text(audio_path)
        
        st.subheader("Transcription Text")
        st.text_area("Transcription", result_text, height=300)
        
        # Generate unique filenames for the downloads
        timestamp = int(time.time())
        pdf_path = f"transcription_{timestamp}.pdf"
        save_text_to_pdf(result_text, pdf_path)
        
        st.download_button(
            label="Download Transcription as PDF",
            data=open(pdf_path, "rb").read(),
            file_name=pdf_path,
            mime="application/pdf"
        )
        
        # Remove temporary files
        os.remove(audio_path)
        os.remove(pdf_path)
        
        st.success("Audio converted to text successfully!")
