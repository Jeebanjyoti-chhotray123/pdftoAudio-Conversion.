import pdfplumber
import pyttsx3

# Load PDF
pdf_path =  r"C:\Users\ASUS\OneDrive\Desktop\pdf.py\sample2.pdf"   # Change to your PDF file
text = ""

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text += page.extract_text() + "\n"

# Initialize TTS engine
engine = pyttsx3.init()

# Optional: Set voice properties
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)  # 0 = male, 1 = female (depends on OS)
engine.setProperty("rate", 150)  # Speed (default ~200)

# Save as MP3
output_file = "output.mp3"
engine.save_to_file(text, output_file)
engine.runAndWait()

print(f"✅ Audio saved as {output_file}")
