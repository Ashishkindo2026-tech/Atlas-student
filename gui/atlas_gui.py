import customtkinter as ctk
import os
import sys
from tkinter import filedialog, messagebox, simpledialog

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.agent import process
from education.ingest import ingest_pdf

# Atlas Student UI — based on the supplied desktop mockup.
# Three desktop themes: Default, Black, White.
THEMES = {
    "default": {
        "bg": "#240B0F", "surface": "#351319", "panel": "#FFF7ED",
        "panel2": "#F1D8C1", "sidebar": "#360B12", "accent": "#D89A20",
        "accent2": "#F1B63B", "text": "#FFF8EF", "dark": "#2A1510",
        "muted": "#D8B9A5", "border": "#6C2B30", "bubble": "#F4E2D0"
    },
    "black": {
        "bg": "#050505", "surface": "#111111", "panel": "#191919",
        "panel2": "#242424", "sidebar": "#160A0C", "accent": "#DCA12D",
        "accent2": "#F2C45B", "text": "#F8F4EE", "dark": "#16110D",
        "muted": "#B8ACA2", "border": "#3C3030", "bubble": "#252525"
    },
    "white": {
        "bg": "#FAF7F1", "surface": "#FFFDF9", "panel": "#FFFFFF",
        "panel2": "#F2E3D1", "sidebar": "#4A0F17", "accent": "#D19A2E",
        "accent2": "#E9B84A", "text": "#2D2020", "dark": "#2D2020",
        "muted": "#7A6C66", "border": "#E1C9B2", "bubble": "#FFF1E2"
    }
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")


class AtlasGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.theme_name = "default"
        self.colors = THEMES[self.theme_name]
        self.title("Atlas Student")
        self.geometry("1280x800")
        self.minsize(1050, 680)
        self.configure(fg_color=self.colors["bg"])
        self._build_shell()
        self.show_home()

    def _build_shell(self):
        self.sidebar = ctk.CTkFrame(self, width=205, fg_color=self.colors["sidebar"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="✦ ATLAS STUDENT", text_color="#E6C17A",
                     font=("Georgia", 13, "bold")).pack(anchor="w", padx=22, pady=(22, 22))

        self.nav = []
        items = [
            ("⌂  Home", self.show_home), ("◉  Chat", self.show_chat),
            ("▣  My Library", self.show_library), ("◎  Memory", self.show_memory),
            ("◇  Goals", self.show_goals), ("▤  Progress", self.show_progress),
            ("◌  Voice", self.show_voice)
        ]
        for text, command in items:
            btn = ctk.CTkButton(self.sidebar, text=text, command=command, anchor="w",
                                fg_color="transparent", hover_color="#5B1821",
                                text_color="#F7E9DF", font=("Segoe UI", 11),
                                height=38, corner_radius=7)
            btn.pack(fill="x", padx=10, pady=2)
            self.nav.append(btn)

        ctk.CTkButton(self.sidebar, text="⚙  Settings", anchor="w",
                      command=self.show_settings, fg_color="transparent",
                      hover_color="#5B1821", text_color="#D5B7AA",
                      font=("Segoe UI", 10), height=38, corner_radius=7).pack(
                          side="bottom", fill="x", padx=10, pady=16)

        self.main = ctk.CTkFrame(self, fg_color=self.colors["bg"], corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def apply_theme(self, name):
        if name not in THEMES:
            return
        self.theme_name = name
        self.colors = THEMES[name]
        self.configure(fg_color=self.colors["bg"])
        self.sidebar.configure(fg_color=self.colors["sidebar"])
        self.main.configure(fg_color=self.colors["bg"])
        self.show_home()

    def topbar(self):
        bar = ctk.CTkFrame(self.main, fg_color="transparent", height=52)
        bar.pack(fill="x", padx=26, pady=(15, 0))
        ctk.CTkLabel(bar, text="Desktop:", text_color=self.colors["muted"],
                     font=("Segoe UI", 10)).pack(side="right", padx=(0, 8))
        for name, label in (("default", "DEFAULT"), ("black", "BLACK"), ("white", "WHITE")):
            ctk.CTkButton(bar, text=label, width=64, height=27, command=lambda n=name: self.apply_theme(n),
                          fg_color=self.colors["surface"] if name != self.theme_name else self.colors["accent"],
                          hover_color=self.colors["accent2"],
                          text_color=self.colors["text"] if name != self.theme_name else self.colors["dark"],
                          font=("Segoe UI", 8, "bold"), corner_radius=6).pack(side="right", padx=3)

    def heading(self, title, subtitle=None):
        self.topbar()
        ctk.CTkLabel(self.main, text=title, text_color=self.colors["text"],
                     font=("Georgia", 26, "bold")).pack(anchor="w", padx=38, pady=(5, 0))
        if subtitle:
            ctk.CTkLabel(self.main, text=subtitle, text_color=self.colors["muted"],
                         font=("Segoe UI", 11)).pack(anchor="w", padx=40, pady=(2, 17))

    def card(self, title, body="", parent=None, compact=False):
        p = parent or self.main
        frame = ctk.CTkFrame(p, fg_color=self.colors["panel"], corner_radius=10,
                             border_width=1, border_color=self.colors["border"])
        ctk.CTkLabel(frame, text=title, text_color=self.colors["dark"],
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 3))
        if body:
            ctk.CTkLabel(frame, text=body, text_color=self.colors["dark"], justify="left",
                         wraplength=350 if compact else 700,
                         font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 12))
        return frame

    def show_home(self):
        self.clear()
        self.heading("Good evening, Ashish.", "What are we learning today?")
        hero = ctk.CTkFrame(self.main, fg_color=self.colors["surface"], corner_radius=14,
                            border_width=1, border_color=self.colors["border"])
        hero.pack(fill="x", padx=38, pady=4)
        ctk.CTkLabel(hero, text="ATLAS", text_color=self.colors["accent2"],
                     font=("Georgia", 11, "bold")).pack(anchor="w", padx=22, pady=(17, 0))
        ctk.CTkLabel(hero, text="A personal learning companion that grows with you.",
                     text_color=self.colors["text"], font=("Georgia", 16, "bold")).pack(anchor="w", padx=22, pady=4)
        ctk.CTkLabel(hero, text="Memory • NCERT Library • Goals • Progress • Voice",
                     text_color=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=22)
        ctk.CTkButton(hero, text="What are you learning today?", command=self.show_chat,
                      fg_color=self.colors["accent"], hover_color=self.colors["accent2"],
                      text_color=self.colors["dark"], height=34, corner_radius=8).pack(anchor="e", padx=20, pady=15)

        row = ctk.CTkFrame(self.main, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=38, pady=17)
        for title, body in [
            ("📚 My Library", "CBSE Classes 9–12\nScience • Mathematics • Social Science\nEnglish • Physics • Chemistry"),
            ("🧠 Memory", "Things I Know\nImportant memories\nLearning history\nPreferences"),
            ("📈 Learning Progress", "Physics      60%\nThermodynamics  60%\nWaves       20%\nStrengths & revision needs")
        ]:
            self.card(title, body, row, compact=True).pack(side="left", fill="both", expand=True, padx=(0, 10))

    def show_chat(self):
        self.clear()
        self.heading("Chat", "Talk naturally with Atlas")
        chat = ctk.CTkTextbox(self.main, fg_color=self.colors["surface"],
                              text_color=self.colors["text"], font=("Segoe UI", 10),
                              corner_radius=12, border_width=1, border_color=self.colors["border"])
        chat.pack(fill="both", expand=True, padx=38)
        chat.insert("end", "Atlas\n\nAtlas responds to the same person it learns from.\n\n")
        row = ctk.CTkFrame(self.main, fg_color="transparent")
        row.pack(fill="x", padx=38, pady=12)
        entry = ctk.CTkEntry(row, placeholder_text="Type a message...", height=40,
                             fg_color=self.colors["surface"], text_color=self.colors["text"],
                             border_color=self.colors["border"])
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def send(event=None):
            text = entry.get().strip()
            if not text:
                return
            chat.insert("end", f"\nYou\n{text}\n")
            entry.delete(0, "end")
            try:
                answer = process(text)
            except Exception as exc:
                answer = f"I couldn't process that yet: {exc}"
            chat.insert("end", f"\nAtlas\n{answer}\n")
            chat.see("end")

        entry.bind("<Return>", send)
        ctk.CTkButton(row, text="＋", command=send, width=40, fg_color=self.colors["surface"],
                      hover_color=self.colors["accent"], text_color=self.colors["text"]).pack(side="right")
        ctk.CTkButton(row, text="🎙", width=40, fg_color=self.colors["accent"],
                      hover_color=self.colors["accent2"], text_color=self.colors["dark"]).pack(side="right", padx=5)

    def show_library(self):
        self.clear()
        self.heading("My Library", "CBSE core • Classes 9–12")
        ctk.CTkButton(self.main, text="＋ Add Book", command=self.add_book,
                      fg_color=self.colors["accent"], hover_color=self.colors["accent2"],
                      text_color=self.colors["dark"], height=34).pack(anchor="w", padx=38, pady=(0, 13))
        grid = ctk.CTkFrame(self.main, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=38)
        subjects = ["Science", "Mathematics", "Social Science", "English", "Physics", "Chemistry", "Biology", "Computer Science"]
        for i, subject in enumerate(subjects):
            level = "Classes 9–12"
            self.card(f"📖 {subject}", f"{level}\nPDF indexed • Searchable\nRead every indexed word", grid, compact=True).grid(
                row=i // 4, column=i % 4, sticky="nsew", padx=5, pady=5)
        for c in range(4): grid.grid_columnconfigure(c, weight=1)
        for r in range(2): grid.grid_rowconfigure(r, weight=1)

    def add_book(self):
        path = filedialog.askopenfilename(title="Choose an authorized textbook PDF",
                                          filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        level = simpledialog.askinteger("Class", "Class (9–12):", minvalue=9, maxvalue=12, parent=self)
        subject = simpledialog.askstring("Subject", "Subject:", parent=self) if level else None
        if not level or not subject:
            return
        try:
            data = ingest_pdf(path, level, subject)
            messagebox.showinfo("Atlas Library", f"Indexed: {data['title']}\nPages: {data['pages_indexed']}")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def show_memory(self):
        self.clear(); self.heading("Memory", "Everything Atlas learns should remain under your control.")
        for title, body in [
            ("Things I Know", "Name • interests • study context"),
            ("Important Memories", "Important conversations and saved facts"),
            ("Learning History", "What you studied, when, and what needs revision"),
            ("Preferences", "How you prefer Atlas to communicate and teach")
        ]:
            self.card(title, body).pack(fill="x", padx=38, pady=5)

    def show_goals(self):
        self.clear(); self.heading("Goals", "Goals should grow from your conversations with Atlas.")
        self.card("Keep building Atlas Student", "Active • Long-term project").pack(fill="x", padx=38, pady=5)
        self.card("Prepare for your next exam", "Atlas can turn your available time and syllabus into a realistic plan.").pack(fill="x", padx=38, pady=5)

    def show_progress(self):
        self.clear(); self.heading("Learning Progress", "A map of what you know and what needs attention.")
        row = ctk.CTkFrame(self.main, fg_color="transparent"); row.pack(fill="both", expand=True, padx=38)
        left = self.card("Strengths", "Physics                 60%\nThermodynamics          60%\nWaves                    20%\n\nConcepts needing revision  30%", row)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.card("Examples", "• Thermodynamics\n  Introduction → studied\n  Heat transfer → needs review\n\n• Recommended topics\n  Based on recent learning", row)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

    def show_voice(self):
        self.clear(); self.heading("Voice", "Hands-free Atlas interaction")
        panel = ctk.CTkFrame(self.main, fg_color=self.colors["panel"], corner_radius=16,
                             border_width=1, border_color=self.colors["border"])
        panel.pack(fill="both", expand=True, padx=38, pady=5)
        ctk.CTkLabel(panel, text="〰  ATLAS  〰", text_color=self.colors["accent"],
                     font=("Georgia", 28, "bold")).pack(pady=(100, 15))
        ctk.CTkLabel(panel, text="Listening...", text_color=self.colors["dark"],
                     font=("Segoe UI", 13)).pack(pady=4)
        ctk.CTkLabel(panel, text="Atlas is thinking...", text_color=self.colors["muted"],
                     font=("Segoe UI", 10)).pack()

    def show_settings(self):
        self.clear(); self.heading("Settings", "Control your Atlas experience.")
        self.card("Desktop appearance", "Use the Default / Black / White controls at the top right.").pack(fill="x", padx=38, pady=5)
        self.card("Privacy", "Atlas should keep personal memory under user control.").pack(fill="x", padx=38, pady=5)


if __name__ == "__main__":
    AtlasGUI().mainloop()
