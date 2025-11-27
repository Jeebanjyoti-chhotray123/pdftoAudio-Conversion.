import pdfplumber
from gtts import gTTS

# Load PDF
pdf_path = r"C:\Users\ASUS\OneDrive\Desktop\pdf.py\sample.pdf.pdf"   # Change to your PDF file
text = ""

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text += page.extract_text() + "\n"

# Convert text to speech
tts = gTTS(text=text, lang="en")
output_file = "output.mp3"
tts.save(output_file)

print(f"✅ Audio saved as {output_file}")
