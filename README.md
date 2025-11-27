# PDF to Audio Conversion 

This project converts text from a PDF file into spoken audio using Python.  
It extracts text from PDF pages and generates an audio output (MP3/WAV format).  
Useful for students, visually impaired users, or anyone who wants to listen to documents instead of reading them.

---

## 🚀 Features
- Convert any PDF file into audio  
- Automatically extracts text from all pages  
- Supports MP3/WAV output  
- Fast and simple process  
- Helpful for reading notes, books, and study material  

project/
│── pdf.py # Main script
│── offline.py # Offline conversion logic
│── online.py # Online / cloud version
│── outputs/ # Folder where audio files are saved
│── requirements.txt # Dependencies


---

## 🛠️ Technologies Used
- **Python 3**
- **PyPDF2** / **pdfplumber** — for PDF text extraction  
- **gTTS** / **pyttsx3** — for text-to-speech  
- **OS / sys** — file handling  

---

## ▶️ How to Run

### **1. Install dependencies**

pip install -r requirements.txt
### **2. Run the script**

python pdf.py

### **3. Select the PDF file**
The script will extract the text and generate an audio file in the **outputs/** folder.

---

## 📦 Requirements
Create a file named **requirements.txt** containing:

pyttsx3
PyPDF2
gTTS
pdfplumber


---

## 📸 Screenshots (optional)
_Add screenshots of your UI or command-line output here._

---

## 📌 Future Improvements
- Add GUI interface  
- Support for multiple languages  
- Add option for different voices  
- Mobile app version  

---

## 👤 Author
**Jeeban Jyoti Chhotray**  
GitHub: https://github.com/JeebanJyoti-chhotray123

---



