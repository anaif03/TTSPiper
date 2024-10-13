import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
from pydub import AudioSegment
from pydub.utils import which

# Configurazione dei percorsi delle dipendenze
PIPER_PATH = r"C:\piper\piper.exe"  # Percorso dell'eseguibile Piper
PIPER_MODEL_PATH = r"C:\piper\it_IT-riccardo-x_low.onnx"  # Percorso del modello Piper
FFMPEG_PATH = r"C:\piper\ffmpeg\bin\ffmpeg.exe"  # Percorso di ffmpeg

# Configura pydub per usare il percorso corretto di ffmpeg
AudioSegment.converter = FFMPEG_PATH

# Funzione per pulire il testo rimuovendo caratteri speciali e spazi multipli
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Rimuovi spazi multipli
    text = text.strip()  # Rimuovi spazi iniziali e finali
    return text

# 1. Funzione per convertire il file Epub in file di testo
def convert_epub_to_txt(epub_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Creare la cartella di output se non esiste

    book = epub.read_epub(epub_path)
    chapter_files = []
    for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
        text = soup.get_text()
        cleaned_text = clean_text(text)  # Pulizia del testo
        if cleaned_text.strip():  # Filtra i contenuti vuoti
            chapter_file = os.path.join(output_dir, f"chapter_{i+1}.txt")
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            chapter_files.append(chapter_file)
    
    print(f"Conversione Epub a file di testo completata. Salvati {len(chapter_files)} capitoli.")
    return chapter_files

# 2. Funzione per convertire i file di testo in WAV usando `type` (uno dopo l'altro)
def convert_txt_to_wav(chapter_files, output_dir):
    wav_files = []
    
    for i, chapter_file in enumerate(chapter_files):
        wav_file = os.path.join(output_dir, f"chapter_{i+1}.wav")
        print(f"Sto creando WAV: {wav_file}")  # Debug
        
        # Usa `type` per leggere il file di testo e passarlo a Piper
        piper_cmd = f'type "{chapter_file}" | "{PIPER_PATH}" --model "{PIPER_MODEL_PATH}" --output_file "{wav_file}"'
        
        try:
            subprocess.run(piper_cmd, shell=True, check=True)
            # Verifica se il file WAV è stato effettivamente creato
            if os.path.exists(wav_file):
                print(f"File WAV creato: {wav_file}")  # Debug
                wav_files.append(wav_file)
            else:
                print(f"File WAV non trovato dopo la creazione con Piper: {wav_file}")
        except subprocess.CalledProcessError as e:
            print(f"Errore nell'esecuzione di Piper TTS per {chapter_file}: {e}")
            continue
    
    print(f"Conversione da file di testo a WAV completata per {len(wav_files)} file.")
    return wav_files

# 3. Funzione per convertire i file WAV in MP3 (uno dopo l'altro)
def convert_wav_to_mp3(wav_files, output_dir):
    mp3_files = []
    
    for wav_file in wav_files:
        # Usa os.path.normpath per gestire correttamente i separatori di percorso
        mp3_file = os.path.normpath(wav_file.replace(".wav", ".mp3"))
        wav_file = os.path.normpath(wav_file)  # Normalizza il percorso del file WAV
        print(f"Sto convertendo WAV in MP3: {wav_file} -> {mp3_file}")  # Debug
        
        try:
            sound = AudioSegment.from_wav(wav_file)
            sound.export(mp3_file, format="mp3")
            mp3_files.append(mp3_file)
        except Exception as e:
            print(f"Errore nella conversione da WAV a MP3 per {wav_file}: {e}")
            continue
    
    print(f"Conversione da WAV a MP3 completata per {len(mp3_files)} file.")
    return mp3_files

# Funzione principale per la conversione
def convert_epub_to_audio(epub_file, output_dir):
    # 1. Convertire l'Epub in file di testo e salvarli
    chapter_files = convert_epub_to_txt(epub_file, output_dir)
    
    # 2. Convertire ogni file di testo in WAV
    wav_files = convert_txt_to_wav(chapter_files, output_dir)
    
    # 3. Convertire ogni file WAV in MP3
    convert_wav_to_mp3(wav_files, output_dir)

# GUI per la selezione dei file e il monitoraggio del progresso
def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("Epub files", "*.epub")])
    if file_path:
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if output_dir:
            threading.Thread(target=convert_epub_to_audio, args=(file_path, output_dir)).start()

def create_gui():
    root = tk.Tk()
    root.title("Epub to Audio Converter")

    label = tk.Label(root, text="Seleziona un file Epub da convertire:")
    label.pack(pady=10)

    select_button = tk.Button(root, text="Select Epub", command=open_file_dialog)
    select_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()

