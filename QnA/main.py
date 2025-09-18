import tkinter as tk
from tkinter import scrolledtext
import threading

class ChatApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("사내 RAG 챗봇")
        self.geometry("600x400")

        self.chat_history = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, bg="#f0f0f0", padx=10, pady=10)
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(self)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.user_input = tk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(input_frame, text="전송", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

    def send_message(self, event=None):
        message = self.user_input.get()
        if message.strip():
            self.add_message("You", message)
            self.user_input.delete(0, tk.END)
            
            # Simulate bot response in a separate thread
            threading.Thread(target=self.get_bot_response, args=(message,), daemon=True).start()
    
    def get_bot_response(self, message):
        # Placeholder for RAG logic
        # For now, just echo the message
        import time
        time.sleep(1) # Simulate network/processing delay
        bot_reply = f"Echo: {message}"
        self.add_message("Bot", bot_reply)


    def add_message(self, sender, message):
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

if __name__ == "__main__":
    app = ChatApplication()
    app.mainloop()
