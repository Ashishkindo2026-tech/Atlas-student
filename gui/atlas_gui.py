import customtkinter as ctk
import os, sys
from tkinter import filedialog, messagebox, simpledialog

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.agent import process
from education.ingest import ingest_pdf

# Atlas Student visual system: warm ivory + charcoal + antique gold.
BG = "#F6F0E6"
SIDEBAR = "#29251F"
PANEL = "#FFF9F0"
CARD = "#EFE5D5"
TEXT = "#29251F"
MUTED = "#756C61"
GOLD = "#B38A3E"
GOLD_HOVER = "#C6A45F"
ENTRY = "#FFFDF8"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")


class AtlasGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atlas Student")
        self.geometry("1200x760")
        self.minsize(980, 650)
        self.configure(fg_color=BG)
        self._build_sidebar()
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)
        self.show_home()

    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR, corner_radius=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        ctk.CTkLabel(side, text="✦ ATLAS", text_color="#E4C98A", font=("Georgia", 25, "bold")).pack(anchor="w", padx=24, pady=(30, 0))
        ctk.CTkLabel(side, text="STUDENT", text_color="#A9A095", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=27, pady=(0, 24))
        items = [("⌂  Home", self.show_home), ("💬  Chat", self.show_chat), ("📚  My Library", self.show_library), ("🧠  Memory", self.show_memory), ("🎯  Goals", self.show_goals), ("📈  Progress", self.show_progress), ("🎙  Voice", self.show_voice)]
        for text, cmd in items:
            ctk.CTkButton(side, text=text, command=cmd, anchor="w", fg_color="transparent", hover_color="#3A342C", text_color="#F4EBDD", font=("Segoe UI", 11), height=40).pack(fill="x", padx=8, pady=2)
        ctk.CTkButton(side, text="⚙  Settings", anchor="w", fg_color="transparent", hover_color="#3A342C", text_color="#A9A095", height=40).pack(side="bottom", fill="x", padx=8, pady=20)

    def clear(self):
        for w in self.main.winfo_children(): w.destroy()

    def heading(self, title, subtitle=None):
        ctk.CTkLabel(self.main, text=title, text_color=TEXT, font=("Georgia", 29, "bold")).pack(anchor="w", padx=42, pady=(34, 0))
        if subtitle:
            ctk.CTkLabel(self.main, text=subtitle, text_color=MUTED, font=("Segoe UI", 11)).pack(anchor="w", padx=44, pady=(2, 22))

    def card(self, title, body="", parent=None):
        p = parent or self.main
        frame = ctk.CTkFrame(p, fg_color=PANEL, corner_radius=14, border_width=1, border_color="#E4D7C5")
        ctk.CTkLabel(frame, text=title, text_color=GOLD, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
        if body:
            ctk.CTkLabel(frame, text=body, text_color=TEXT, justify="left", wraplength=500, font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 16))
        return frame

    def show_home(self):
        self.clear(); self.heading("Good evening, Ashish.", "What are we learning today?")
        hero = ctk.CTkFrame(self.main, fg_color=PANEL, corner_radius=18, border_width=1, border_color="#E4D7C5")
        hero.pack(fill="x", padx=42)
        ctk.CTkLabel(hero, text="✦", text_color=GOLD, font=("Georgia", 34)).pack(anchor="w", padx=28, pady=(22, 0))
        ctk.CTkLabel(hero, text="Your learning, memories and goals — together.", text_color=TEXT, font=("Georgia", 19, "bold")).pack(anchor="w", padx=28, pady=5)
        ctk.CTkLabel(hero, text="Atlas Student is ready.", text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=28)
        ctk.CTkButton(hero, text="Start a conversation  →", command=self.show_chat, fg_color=GOLD, hover_color=GOLD_HOVER, text_color="#20170E", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=28, pady=20)
        row = ctk.CTkFrame(self.main, fg_color="transparent")
        row.pack(fill="x", padx=42, pady=20)
        for title, body in [("📚 Continue learning", "Class 11 • Physics"), ("🎯 Goals", "Keep building Atlas Student"), ("📈 Progress", "Your learning profile is growing")]:
            self.card(title, body, row).pack(side="left", fill="both", expand=True, padx=(0, 12))

    def show_chat(self):
        self.clear(); self.heading("Atlas", "Ask, learn, plan.")
        chat = ctk.CTkTextbox(self.main, fg_color=PANEL, text_color=TEXT, font=("Segoe UI", 11), corner_radius=14, border_width=1, border_color="#E4D7C5")
        chat.pack(fill="both", expand=True, padx=42)
        chat.insert("end", "Atlas\n\nWhat would you like to learn or work on?\n")
        row = ctk.CTkFrame(self.main, fg_color="transparent")
        row.pack(fill="x", padx=42, pady=12)
        entry = ctk.CTkEntry(row, placeholder_text="Ask Atlas anything...", height=42, fg_color=ENTRY, border_color="#D8C8B2", text_color=TEXT)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        def send(event=None):
            text = entry.get().strip()
            if not text: return
            chat.insert("end", f"\nYou\n{text}\n")
            entry.delete(0, "end")
            try: answer = process(text)
            except Exception as exc: answer = f"I couldn't process that yet: {exc}"
            chat.insert("end", f"\nAtlas\n{answer}\n")
            chat.see("end")
        entry.bind("<Return>", send)
        ctk.CTkButton(row, text="Send  →", command=send, width=100, fg_color=GOLD, hover_color=GOLD_HOVER, text_color="#20170E").pack()

    def show_library(self):
        self.clear(); self.heading("My Library", "CBSE core • Classes 9–12")
        ctk.CTkButton(self.main, text="＋ Add Book PDF", command=self.add_book, fg_color=GOLD, hover_color=GOLD_HOVER, text_color="#20170E", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=42, pady=(0, 18))
        for level in (9, 10, 11, 12):
            self.card(f"Class {level}", f"Authorized PDFs • education/library/core/class{level}/<subject>/").pack(fill="x", padx=42, pady=5)

    def add_book(self):
        path = filedialog.askopenfilename(title="Choose an authorized textbook PDF", filetypes=[("PDF files", "*.pdf")])
        if not path: return
        level = simpledialog.askinteger("Class", "Class (9–12):", minvalue=9, maxvalue=12, parent=self)
        subject = simpledialog.askstring("Subject", "Subject:", parent=self) if level else None
        if not level or not subject: return
        try:
            data = ingest_pdf(path, level, subject)
            messagebox.showinfo("Atlas Library", f"Indexed: {data['title']}\nPages: {data['pages_indexed']}")
        except Exception as exc: messagebox.showerror("Import failed", str(exc))

    def simple(self, title, text):
        self.clear(); self.heading(title); self.card(title, text).pack(fill="x", padx=42)
    def show_memory(self): self.simple("Memory", "Your memories belong to you.\n\nMemory controls will appear here.")
    def show_goals(self): self.simple("Goals", "Your active Atlas goals will appear here.")
    def show_progress(self): self.simple("Learning Progress", "Strengths, revision needs and concept mastery will appear here.")
    def show_voice(self): self.simple("Voice", "🎙 Voice interaction\n\nYour existing Atlas voice engine can be connected here.")


if __name__ == "__main__":
    AtlasGUI().mainloop()
