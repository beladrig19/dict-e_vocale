import sys
import queue
import threading
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Chemin vers le modèle de langue
model_path = "/home/patrick/projets_data/dictèe_vocale/vosk-model-small-fr-0.22"


# Initialisation du modèle
model = Model(model_path)

class VoiceDictationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dictée Vocale")
        self.is_listening = False

        # Création des widgets
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.start_button = tk.Button(root, text="Démarrer la dictée", command=self.start_listening)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Arrêter la dictée", command=self.stop_listening, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # File d'attente pour les données audio
        self.audio_queue = queue.Queue()
        self.recognizer = KaldiRecognizer(model, 16000)
        self.audio_stream = None

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Problème audio : {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.text_area.insert(tk.END, "Dictée vocale en cours...\n")
            threading.Thread(target=self.listen_and_recognize).start()

    def stop_listening(self):
        if self.is_listening:
            self.is_listening = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
            self.text_area.insert(tk.END, "Dictée vocale arrêtée.\n")

    def listen_and_recognize(self):
        try:
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                   channels=1, callback=self.audio_callback):
                self.audio_stream = sd
                while self.is_listening:
                    data = self.audio_queue.get()
                    if self.recognizer.AcceptWaveform(data):
                        result = self.recognizer.Result()
                        text = json.loads(result)['text']
                        if text:
                            self.text_area.insert(tk.END, text + "\n")
                            self.text_area.see(tk.END)
                    else:
                        partial_result = self.recognizer.PartialResult()
                        # Affichage en temps réel non implémenté ici
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")
            self.stop_listening()

# Exécution de l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceDictationApp(root)
    root.mainloop()