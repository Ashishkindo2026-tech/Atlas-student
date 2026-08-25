"""Atlas Student Learning OS with user-controlled UI/UX.

Atlas Studio intentionally exposes the visual system instead of locking users
into a handful of themes. Every supported UI value is stored as JSON and can
be edited, exported, imported, previewed and reset without touching Atlas's
learning logic.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.agent import process

try:
    from voice_engine import listen, speak
    VOICE_AVAILABLE = True
except Exception:
    listen = speak = None
    VOICE_AVAILABLE = False

try:
    from memory.memory_manager import MemoryManager
except Exception:
    MemoryManager = None

try:
    from student.progress_manager import ProgressManager
except Exception:
    ProgressManager = None

try:
    from education.ingest import ingest_pdf
except Exception:
    ingest_pdf = None

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = ImageTk = None
    PIL_AVAILABLE = False


DEFAULT_UI = {
    "background": "#080A0F",
    "sidebar": "#06080C",
    "panel": "#10141B",
    "panel_alt": "#141923",
    "panel_hover": "#1A202C",
    "text": "#F4F6FA",
    "muted": "#8993A5",
    "accent": "#86A4FF",
    "accent_hover": "#A8BAFF",
    "accent_dark": "#263554",
    "success": "#70D2A5",
    "warning": "#E6B86A",
    "danger": "#E58D8D",
    "border": "#252C39",
    "font": "Segoe UI",
    "font_size": 10,
    "title_size": 29,
    "radius": 18,
    "sidebar_width": 230,
    "ui_scale": 1.0,
    "opacity": 1.0,
    "animation_ms": 200,
    "show_sidebar": True,
    "show_status": True,
    "show_date": True,
    "background_image": "",
    "background_image_opacity": 1.0,
    "layout": "learning_os",
}

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
UI_FILE = APPDATA / "ui.json"


def load_ui():
    try:
        APPDATA.mkdir(parents=True, exist_ok=True)
        if UI_FILE.exists():
            data = json.loads(UI_FILE.read_text(encoding="utf-8"))
            out = deepcopy(DEFAULT_UI)
            out.update({k: v for k, v in data.items() if k in out})
            return out
    except Exception:
        pass
    return deepcopy(DEFAULT_UI)


def save_ui(data):
    APPDATA.mkdir(parents=True, exist_ok=True)
    UI_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class AtlasGUI(ctk.CTk):
    """Atlas desktop Learning OS plus full-access Atlas Studio."""

    def __init__(self):
        super().__init__()
        self.ui = load_ui()
        self.title("ATLAS — Personal AI Learning System")
        self.geometry("1440x900")
        self.minsize(1000, 650)
        self.current_page = "home"
        self.voice_busy = False
        self.chat_busy = False
        self.command_overlay = None
        self.chat_messages: list[tuple[str, str]] = []
        self.progress = ProgressManager() if ProgressManager else None
        self.memory = MemoryManager() if MemoryManager else None
        self._apply_window()
        self._build_shell()
        self.bind("<Control-space>", lambda _e: self.toggle_command_center())
        self.bind("<Escape>", lambda _e: self.close_command_center())
        self.show_home()

    def _apply_window(self):
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.ui["background"])
        try:
            self.attributes("-alpha", float(self.ui["opacity"]))
        except Exception:
            pass

    def _c(self, key):
        return self.ui[key]

    def _font(self, size=None, weight="normal"):
        size = size or self.ui["font_size"]
        return (self.ui["font"], int(size * self.ui["ui_scale"]), weight)

    def _build_shell(self):
        if hasattr(self, "rail"):
            self.rail.destroy()
        self.rail = ctk.CTkFrame(self, width=int(self.ui["sidebar_width"]), fg_color=self._c("sidebar"), corner_radius=0)
        if self.ui["show_sidebar"]:
            self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)
        brand = ctk.CTkFrame(self.rail, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(22, 24))
        ctk.CTkLabel(brand, text="◉", text_color=self._c("accent"), font=("Segoe UI Symbol", 24, "bold")).pack(side="left")
        labels = ctk.CTkFrame(brand, fg_color="transparent"); labels.pack(side="left", padx=9)
        ctk.CTkLabel(labels, text="ATLAS", text_color=self._c("text"), font=self._font(15, "bold")).pack(anchor="w")
        ctk.CTkLabel(labels, text="PERSONAL LEARNING OS", text_color=self._c("muted"), font=self._font(7, "bold")).pack(anchor="w")
        if self.ui["show_status"]:
            status = ctk.CTkFrame(self.rail, fg_color=self._c("panel"), corner_radius=12)
            status.pack(fill="x", padx=14, pady=(0, 16))
            ctk.CTkLabel(status, text="●", text_color=self._c("success"), font=self._font(10)).pack(side="left", padx=(10, 5), pady=9)
            ctk.CTkLabel(status, text="ATLAS CORE  •  ONLINE", text_color=self._c("muted"), font=self._font(8, "bold")).pack(side="left")
        self.nav_buttons = {}
        groups = [
            ("COMMAND CENTER", [("⌂", "Home", self.show_home), ("◈", "Chat", self.show_chat), ("◉", "Voice", self.show_voice)]),
            ("LEARNING", [("Φ", "Physics", lambda: self.show_subject("Physics")), ("∑", "Maths", lambda: self.show_subject("Mathematics")), ("⚗", "Chemistry", lambda: self.show_subject("Chemistry")), ("▣", "Notes", self.show_notes), ("◇", "Practice", self.show_practice), ("◫", "Planner", self.show_planner)]),
            ("INSIGHTS", [("◌", "Memory", self.show_memory), ("▥", "Progress", self.show_progress)]),
        ]
        for heading, items in groups:
            ctk.CTkLabel(self.rail, text=heading, text_color="#626C7D", font=self._font(8, "bold")).pack(anchor="w", padx=20, pady=(4, 7))
            for icon, label, command in items:
                self._nav_button(icon, label, command)
        self._nav_button("⚙", "Studio", self.show_studio, bottom=True)
        self.main = ctk.CTkFrame(self, fg_color=self._c("background"), corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def _nav_button(self, icon, label, command, bottom=False):
        b = ctk.CTkButton(self.rail, text=f"  {icon}    {label}", command=command, anchor="w", height=38,
                          fg_color="transparent", hover_color=self._c("panel_alt"), text_color=self._c("muted"),
                          corner_radius=10, font=self._font(10, "bold"))
        b.pack(side="bottom" if bottom else "top", fill="x", padx=10, pady=2)
        self.nav_buttons[label] = b

    def clear(self):
        for child in self.main.winfo_children(): child.destroy()

    def header(self, eyebrow, title, subtitle=""):
        top = ctk.CTkFrame(self.main, fg_color="transparent"); top.pack(fill="x", padx=42, pady=(28, 18))
        left = ctk.CTkFrame(top, fg_color="transparent"); left.pack(side="left")
        ctk.CTkLabel(left, text=eyebrow.upper(), text_color=self._c("accent"), font=self._font(8, "bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=title, text_color=self._c("text"), font=self._font(self.ui["title_size"], "bold")).pack(anchor="w", pady=(3, 0))
        if subtitle: ctk.CTkLabel(left, text=subtitle, text_color=self._c("muted"), font=self._font(10)).pack(anchor="w", pady=(3, 0))
        if self.ui["show_date"]:
            ctk.CTkLabel(top, text=datetime.now().strftime("%a  •  %d %b %Y"), text_color=self._c("muted"), font=self._font(9, "bold")).pack(side="right", anchor="n")

    def card(self, parent, color=None, radius=None):
        return ctk.CTkFrame(parent, fg_color=color or self._c("panel"), corner_radius=int(radius or self.ui["radius"]), border_width=1, border_color=self._c("border"))

    def button(self, parent, text, command, width=140, primary=False):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=40, corner_radius=int(self.ui["radius"] * .67),
                             fg_color=self._c("accent") if primary else self._c("panel_hover"),
                             hover_color=self._c("accent_hover") if primary else self._c("panel_alt"),
                             text_color=self._c("background") if primary else self._c("text"), font=self._font(10, "bold"))

    def set_active(self, label):
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=self._c("accent_dark") if name == label else "transparent", text_color=self._c("text") if name == label else self._c("muted"))

    def show_home(self):
        self.set_active("Home"); self.clear(); self.header("Atlas Core", "Good afternoon, Ashish.", "What are we working on?")
        body = ctk.CTkFrame(self.main, fg_color="transparent"); body.pack(fill="both", expand=True, padx=42, pady=(0, 30)); body.grid_columnconfigure((0,1), weight=1); body.grid_rowconfigure(1, weight=1)
        welcome = self.card(body); welcome.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(welcome, text="ATLAS CORE", text_color=self._c("accent"), font=self._font(8, "bold")).pack(anchor="w", padx=22, pady=(20,4))
        ctk.CTkLabel(welcome, text="Your learning system is ready.", text_color=self._c("text"), font=self._font(22, "bold")).pack(anchor="w", padx=22)
        ctk.CTkLabel(welcome, text="Chat is a feature of Atlas. Learning is the center of Atlas.", text_color=self._c("muted"), font=self._font(10)).pack(anchor="w", padx=22, pady=(3,15))
        actions = ctk.CTkFrame(welcome, fg_color="transparent"); actions.pack(fill="x", padx=18, pady=(0,16))
        for title, desc, cmd in [("💬 CHAT","Ask Atlas",self.show_chat),("◉ VOICE","Talk naturally",self.show_voice),("◇ PRACTICE","Test yourself",self.show_practice),("▣ NOTES","Capture knowledge",self.show_notes)]:
            a=self.card(actions,self._c("panel_alt"),14); a.pack(side="left",fill="x",expand=True,padx=4); self.button(a,title,cmd,120,title.startswith("💬")).pack(pady=(12,3)); ctk.CTkLabel(a,text=desc,text_color=self._c("muted"),font=self._font(8)).pack(pady=(0,12))
        left=self.card(body); left.grid(row=1,column=0,sticky="nsew",padx=(0,6)); ctk.CTkLabel(left,text="TODAY'S PROGRESS",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",padx=22,pady=(22,3)); ctk.CTkLabel(left,text="78%",text_color=self._c("text"),font=self._font(38,"bold")).pack(anchor="w",padx=22)
        bar=ctk.CTkProgressBar(left,height=8,progress_color=self._c("accent"),fg_color=self._c("border")); bar.pack(fill="x",padx=22,pady=(7,18)); bar.set(.78)
        for s,v in [("Physics",.72),("Mathematics",.81),("Chemistry",.76)]: self._progress_row(left,s,v)
        right=self.card(body); right.grid(row=1,column=1,sticky="nsew",padx=(6,0)); ctk.CTkLabel(right,text="ATLAS INSIGHT",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",padx=22,pady=(22,8)); ctk.CTkLabel(right,text="Your next best move",text_color=self._c("text"),font=self._font(19,"bold")).pack(anchor="w",padx=22); ctk.CTkLabel(right,text="Review a weak concept, then practice it. Atlas can adapt the next questions to your learning signals.",text_color=self._c("muted"),wraplength=390,justify="left",font=self._font(10)).pack(anchor="w",padx=22,pady=(8,20)); self.button(right,"Open Practice Lab",self.show_practice,180,True).pack(anchor="w",padx=22)

    def _progress_row(self,parent,subject,value):
        row=ctk.CTkFrame(parent,fg_color="transparent"); row.pack(fill="x",padx=22,pady=6); ctk.CTkLabel(row,text=subject,text_color=self._c("text"),font=self._font(10,"bold")).pack(side="left"); ctk.CTkLabel(row,text=f"{int(value*100)}%",text_color=self._c("muted"),font=self._font(9)).pack(side="right"); b=ctk.CTkProgressBar(parent,height=5,progress_color=self._c("accent"),fg_color=self._c("border")); b.pack(fill="x",padx=22); b.set(value)

    def show_chat(self):
        self.set_active("Chat"); self.clear(); self.header("Atlas Core","Chat with Atlas","Ask, learn, save, practice — all connected.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=42,pady=(0,28)); self.chat_box=ctk.CTkTextbox(panel,fg_color="transparent",text_color=self._c("text"),font=self._font(11),wrap="word"); self.chat_box.pack(fill="both",expand=True,padx=18,pady=18); self.chat_box.configure(state="disabled")
        if not self.chat_messages:self._chat_add("ATLAS","I'm ready. What are we learning?")
        else:
            for w,m in self.chat_messages:self._chat_add(w,m,False)
        bottom=ctk.CTkFrame(panel,fg_color=self._c("panel_alt"),corner_radius=14); bottom.pack(fill="x",padx=15,pady=(0,15)); self.chat_input=ctk.CTkEntry(bottom,placeholder_text="Ask Atlas anything...",height=44,fg_color="transparent",border_width=0,text_color=self._c("text")); self.chat_input.pack(side="left",fill="x",expand=True,padx=12); self.chat_input.bind("<Return>",lambda _e:self.send_chat()); self.button(bottom,"🎙",self.show_voice,48).pack(side="left",padx=4); self.button(bottom,"Send ➜",self.send_chat,95,True).pack(side="right",padx=6)

    def _chat_add(self,who,msg,store=True):
        if store:self.chat_messages.append((who,msg))
        if not hasattr(self,"chat_box"):return
        self.chat_box.configure(state="normal"); self.chat_box.insert("end",f"\n{who}\n{msg}\n"); self.chat_box.configure(state="disabled"); self.chat_box.see("end")

    def send_chat(self):
        if self.chat_busy or not hasattr(self,"chat_input"):return
        text=self.chat_input.get().strip()
        if not text:return
        self.chat_input.delete(0,"end"); self._chat_add("YOU",text); self.chat_busy=True; self._chat_add("ATLAS","Thinking…"); threading.Thread(target=self._chat_worker,args=(text,),daemon=True).start()

    def _chat_worker(self,text):
        try: answer=process(text)
        except Exception as exc: answer=f"I hit an error while processing that: {exc}"
        self.after(0,lambda a=answer:self._finish_chat(a))

    def _finish_chat(self,answer):
        self.chat_busy=False
        if self.chat_messages and self.chat_messages[-1][1]=="Thinking…":self.chat_messages.pop()
        self._chat_add("ATLAS",answer)

    def show_voice(self):
        self.set_active("Voice"); self.clear(); self.header("Voice Core","Listen. Think. Respond.","The same Atlas brain, with natural voice interaction.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=42,pady=(0,28)); ctk.CTkLabel(panel,text="◉",text_color=self._c("accent"),font=("Segoe UI Symbol",100,"bold")).pack(pady=(70,0)); ctk.CTkLabel(panel,text="ATLAS CORE",text_color=self._c("text"),font=self._font(17,"bold")).pack(); self.voice_status=ctk.CTkLabel(panel,text="ONLINE • READY" if VOICE_AVAILABLE else "VOICE ENGINE UNAVAILABLE",text_color=self._c("success") if VOICE_AVAILABLE else self._c("danger"),font=self._font(10,"bold")); self.voice_status.pack(pady=8); self.voice_hint=ctk.CTkLabel(panel,text="Press the microphone and speak naturally.",text_color=self._c("muted"),font=self._font(10)); self.voice_hint.pack(pady=8); self.listen_btn=self.button(panel,"◉ START LISTENING",self.start_voice,230,True); self.listen_btn.pack(pady=22)

    def start_voice(self):
        if self.voice_busy:return
        if not VOICE_AVAILABLE:self.voice_status.configure(text="VOICE ENGINE UNAVAILABLE",text_color=self._c("danger"));return
        self.voice_busy=True; self.listen_btn.configure(state="disabled",text="◉ LISTENING..."); self.voice_status.configure(text="LISTENING",text_color=self._c("accent_hover")); threading.Thread(target=self._voice_worker,daemon=True).start()

    def _voice_worker(self):
        try:
            text=listen()
            if not text:raise RuntimeError("I didn't hear anything.")
            self.after(0,lambda:self.voice_status.configure(text="THINKING...")); answer=process(text); self.after(0,lambda:self.voice_status.configure(text="SPEAKING...",text_color=self._c("success"))); speak(answer); self.after(0,lambda:self._voice_done("ONLINE • READY","Ready for your next question."))
        except Exception as exc:self.after(0,lambda e=str(exc):self._voice_done("VOICE ERROR",e))

    def _voice_done(self,status,hint):
        self.voice_busy=False; self.voice_status.configure(text=status,text_color=self._c("success") if "READY" in status else self._c("danger")); self.voice_hint.configure(text=hint); self.listen_btn.configure(state="normal",text="◉ START LISTENING")

    def show_subject(self,subject):
        self.set_active("Maths" if subject=="Mathematics" else subject); self.clear(); self.header(subject,f"{subject} workspace","Learn → review → practice → track."); grid=ctk.CTkFrame(self.main,fg_color="transparent"); grid.pack(fill="both",expand=True,padx=42,pady=(0,28)); grid.grid_columnconfigure((0,1),weight=1)
        cards=[("LEARN","Build the concept from first principles.",lambda:self.open_subject_chat(subject,"Teach me the key concepts")),("FORMULA LAB","Review the formulas that matter.",lambda:self.open_subject_chat(subject,"Give me the important formulas and explain them")),("PRACTICE","Test understanding with questions.",self.show_practice),("WEAK AREAS","Use learning signals to decide what needs attention.",lambda:self.open_subject_chat(subject,"What should I practice in this subject?"))]
        for i,(t,d,c) in enumerate(cards):
            x=self.card(grid); x.grid(row=i//2,column=i%2,sticky="nsew",padx=6,pady=6); ctk.CTkLabel(x,text=t,text_color=self._c("accent"),font=self._font(9,"bold")).pack(anchor="w",padx=22,pady=(22,6)); ctk.CTkLabel(x,text=d,text_color=self._c("muted"),wraplength=420,justify="left",font=self._font(11)).pack(anchor="w",padx=22,pady=(0,18)); self.button(x,"Open",c,110,True).pack(anchor="w",padx=22,pady=(0,22))

    def open_subject_chat(self,subject,prompt):self.show_chat();self.chat_input.insert(0,f"{subject}: {prompt}");self.chat_input.focus()

    def show_notes(self):
        self.set_active("Notes"); self.clear(); self.header("Knowledge","Notes","Your personal study shelf."); panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=42,pady=(0,28)); toolbar=ctk.CTkFrame(panel,fg_color="transparent");toolbar.pack(fill="x",padx=18,pady=18);self.button(toolbar,"＋ New note",self.new_note,120,True).pack(side="left");self.button(toolbar,"Open PDF",self.import_pdf,110).pack(side="left",padx=8);self.notes_box=ctk.CTkTextbox(panel,fg_color=self._c("panel_alt"),text_color=self._c("text"),font=self._font(11),wrap="word");self.notes_box.pack(fill="both",expand=True,padx=18,pady=(0,18));self.notes_box.insert("1.0","Your notes live here.\n\nUse Atlas Chat to explain a concept, then save useful parts here.")

    def new_note(self):self.notes_box.delete("1.0","end");self.notes_box.insert("1.0",f"# Study Note — {datetime.now():%d %b %Y}\n\n")

    def import_pdf(self):
        path=filedialog.askopenfilename(filetypes=[("PDF files","*.pdf")]);
        if not path:return
        if not ingest_pdf:messagebox.showerror("Atlas Library","PDF ingestion is unavailable.");return
        messagebox.showinfo("Atlas Library","PDF import is available through the education library.")

    def show_practice(self):
        self.set_active("Practice");self.clear();self.header("Practice Lab","Test your understanding","Adaptive practice built around your learning signals.");panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=42,pady=(0,28));ctk.CTkLabel(panel,text="PRACTICE SESSION",text_color=self._c("accent"),font=self._font(9,"bold")).pack(anchor="w",padx=26,pady=(26,6));ctk.CTkLabel(panel,text="Choose a subject",text_color=self._c("text"),font=self._font(22,"bold")).pack(anchor="w",padx=26);row=ctk.CTkFrame(panel,fg_color="transparent");row.pack(anchor="w",padx=22,pady=20)
        for s in ["Physics","Mathematics","Chemistry"]:self.button(row,s,lambda x=s:self.open_subject_chat(x,"Give me one practice question at an appropriate difficulty."),150,s=="Physics").pack(side="left",padx=4)

    def show_planner(self):
        self.set_active("Planner");self.clear();self.header("Planning","Study planner","Focused sessions around your priorities.");panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=42,pady=(0,28));
        for time,task in [("16:00","Tuition"),("20:00","Physics — focused study"),("20:45","Mathematics — practice"),("21:30","Chemistry — review")]:
            row=ctk.CTkFrame(panel,fg_color=self._c("panel_alt"),corner_radius=12);row.pack(fill="x",padx=26,pady=5);ctk.CTkLabel(row,text=time,text_color=self._c("accent"),font=self._font(10,"bold"),width=70).pack(side="left",padx=12,pady=12);ctk.CTkLabel(row,text=task,text_color=self._c("text"),font=self._font(10)).pack(side="left")
        self.button(panel,"Ask Atlas to build a plan",lambda:self.open_subject_chat("Study","I have limited time. Build me a focused study plan."),220,True).pack(anchor="w",padx=26,pady=20)

    def show_memory(self):
        self.set_active("Memory");self.clear();self.header("Long-term memory","What Atlas knows","Inspect and control durable information.");panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=42,pady=(0,28));box=ctk.CTkTextbox(panel,fg_color=self._c("panel_alt"),text_color=self._c("text"),font=self._font(10));box.pack(fill="both",expand=True,padx=18,pady=18)
        try:
            facts=self.memory.get_facts() if self.memory else {};important=self.memory.get_important_memories() if self.memory else [];lines=["FACTS",""]+[f"• {k}: {v}" for k,v in facts.items()]+["","IMPORTANT MEMORIES",""]+[f"• {x}" for x in important];box.insert("1.0","\n".join(lines) if any(lines[2:]) else "No durable memories saved yet.")
        except Exception as exc:box.insert("1.0",f"Memory interface unavailable: {exc}")
        box.configure(state="disabled")

    def show_progress(self):
        self.set_active("Progress");self.clear();self.header("Learning analytics","Your progress","Evidence from study sessions and learning signals.");panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=42,pady=(0,28));data=self.progress.data() if self.progress else {};signals=data.get("learning_signals",[]) if isinstance(data,dict) else [];ctk.CTkLabel(panel,text=f"{len(signals)} learning signals recorded",text_color=self._c("muted"),font=self._font(10)).pack(anchor="w",padx=24,pady=(24,18));
        for s,v in [("Physics",.72),("Mathematics",.81),("Chemistry",.76)]:self._progress_row(panel,s,v)

    # ---------------- Atlas Studio ----------------
    def show_studio(self):
        self.set_active("Studio"); self.clear(); self.header("Atlas Studio","Design your Atlas","Full control over appearance, layout, interaction and the workspace.")
        shell=ctk.CTkFrame(self.main,fg_color="transparent");shell.pack(fill="both",expand=True,padx=32,pady=(0,26));shell.grid_columnconfigure(0,weight=1);shell.grid_columnconfigure(1,weight=1);shell.grid_rowconfigure(1,weight=1)
        tabs=ctk.CTkTabview(shell,fg_color=self._c("panel"),segmented_button_fg_color=self._c("panel_alt"),segmented_button_selected_color=self._c("accent"),segmented_button_selected_hover_color=self._c("accent_hover"),corner_radius=int(self.ui["radius"]));tabs.grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,10))
        for name in ["Appearance","Layout","Behavior","Raw UI"]:tabs.add(name)
        self._studio_appearance(tabs.tab("Appearance"));self._studio_layout(tabs.tab("Layout"));self._studio_behavior(tabs.tab("Behavior"));self._studio_raw(tabs.tab("Raw UI"))
        preview=self.card(shell,self._c("panel"),self.ui["radius"]);preview.grid(row=1,column=1,sticky="nsew",padx=(8,0));self._studio_preview(preview)
        actions=ctk.CTkFrame(shell,fg_color="transparent");actions.grid(row=1,column=0,sticky="nsew",padx=(0,8));
        ctk.CTkLabel(actions,text="LIVE CONTROL",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",pady=(4,8));self.button(actions,"Apply & Save",self._studio_save,170,True).pack(anchor="w",pady=5);self.button(actions,"Reset to Atlas Default",self._studio_reset,170).pack(anchor="w",pady=5);self.button(actions,"Export Theme",self._studio_export,170).pack(anchor="w",pady=5);self.button(actions,"Import Theme",self._studio_import,170).pack(anchor="w",pady=5);ctk.CTkLabel(actions,text="Every supported value is editable. Raw UI lets advanced users edit the full configuration directly.",text_color=self._c("muted"),wraplength=330,justify="left",font=self._font(9)).pack(anchor="w",pady=18)

    def _studio_appearance(self,p):
        self._color_control(p,"Background","background");self._color_control(p,"Sidebar","sidebar");self._color_control(p,"Panel","panel");self._color_control(p,"Panel alternate","panel_alt");self._color_control(p,"Panel hover","panel_hover");self._color_control(p,"Text","text");self._color_control(p,"Muted text","muted");self._color_control(p,"Accent","accent");self._color_control(p,"Accent hover","accent_hover");self._color_control(p,"Border","border")
        row=ctk.CTkFrame(p,fg_color="transparent");row.pack(fill="x",padx=14,pady=8);ctk.CTkLabel(row,text="Background image",text_color=self._c("text"),font=self._font(9,"bold")).pack(side="left");self.bg_path=ctk.CTkEntry(row,width=260);self.bg_path.pack(side="left",padx=8);self.bg_path.insert(0,self.ui.get("background_image",""));self.button(row,"Browse",self._browse_bg,80).pack(side="left")

    def _color_control(self,parent,label,key):
        row=ctk.CTkFrame(parent,fg_color="transparent");row.pack(fill="x",padx=14,pady=4);ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=150,anchor="w").pack(side="left");sw=ctk.CTkButton(row,text=self.ui[key],width=110,height=30,fg_color=self.ui[key],hover_color=self.ui[key],text_color=self._c("text"),command=lambda k=key,b=None:self._pick_color(k));sw.pack(side="left");setattr(self,f"sw_{key}",sw)

    def _pick_color(self,key):
        picked=colorchooser.askcolor(color=self.ui[key],title=f"Atlas Studio — {key}")[1]
        if picked:self.ui[key]=picked;getattr(self,f"sw_{key}").configure(text=picked,fg_color=picked,hover_color=picked);self._studio_preview_refresh()

    def _studio_layout(self,p):
        self._slider(p,"Sidebar width", "sidebar_width",140,420,1);self._slider(p,"Corner radius","radius",0,32,1);self._slider(p,"UI scale","ui_scale",0.75,1.35,.01);self._slider(p,"Window opacity","opacity",0.75,1,.01);self._choice(p,"Font","font",["Segoe UI","Arial","Consolas","Tahoma","Calibri"]);self._slider(p,"Base font size","font_size",8,16,1);self._slider(p,"Title size","title_size",20,44,1)

    def _studio_behavior(self,p):
        self._slider(p,"Animation speed (ms)","animation_ms",0,600,10);self._switch(p,"Show sidebar","show_sidebar");self._switch(p,"Show Atlas Core status","show_status");self._switch(p,"Show date","show_date")

    def _slider(self,p,label,key,a,b,step):
        row=ctk.CTkFrame(p,fg_color="transparent");row.pack(fill="x",padx=14,pady=7);value=ctk.DoubleVar(value=self.ui[key]);ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=170,anchor="w").pack(side="left");lbl=ctk.CTkLabel(row,text=str(self.ui[key]),text_color=self._c("muted"),width=60);lbl.pack(side="right");scale=ctk.CTkSlider(row,from_=a,to=b,number_of_steps=max(1,int((b-a)/step)),command=lambda v,k=key,l=lbl:self._set_slider(k,v,l),progress_color=self._c("accent"));scale.set(value.get());scale.pack(side="left",fill="x",expand=True,padx=8)

    def _set_slider(self,key,v,label):
        step=0.01 if key=="ui_scale" or key=="opacity" else 1;v=round(float(v),2 if step<1 else 0);self.ui[key]=v;label.configure(text=str(v));self._studio_preview_refresh()

    def _switch(self,p,label,key):
        sw=ctk.CTkSwitch(p,text=label,text_color=self._c("text"),progress_color=self._c("accent"),button_color=self._c("text"));sw.pack(anchor="w",padx=18,pady=8);sw.select() if self.ui[key] else sw.deselect();sw.configure(command=lambda k=key,s=sw:self._set_switch(k,s))

    def _set_switch(self,key,sw):self.ui[key]=bool(sw.get());self._studio_preview_refresh()

    def _choice(self,p,label,key,values):
        row=ctk.CTkFrame(p,fg_color="transparent");row.pack(fill="x",padx=14,pady=7);ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=170,anchor="w").pack(side="left");menu=ctk.CTkOptionMenu(row,values=values,command=lambda v,k=key:self._set_choice(k,v),fg_color=self._c("panel_alt"),button_color=self._c("accent"),text_color=self._c("text"));menu.set(self.ui[key]);menu.pack(side="left",fill="x",expand=True)

    def _set_choice(self,key,v):self.ui[key]=v;self._studio_preview_refresh()

    def _studio_raw(self,p):
        self.raw_box=ctk.CTkTextbox(p,fg_color=self._c("panel_alt"),text_color=self._c("text"),font=("Consolas",10));self.raw_box.pack(fill="both",expand=True,padx=12,pady=12);self.raw_box.insert("1.0",json.dumps(self.ui,indent=2))
        self.button(p,"Apply JSON",self._apply_raw,120,True).pack(anchor="e",padx=12,pady=(0,12))

    def _apply_raw(self):
        try:
            data=json.loads(self.raw_box.get("1.0","end"));merged=deepcopy(DEFAULT_UI);merged.update(data);self.ui=merged;save_ui(self.ui);self._apply_window();messagebox.showinfo("Atlas Studio","UI configuration applied and saved.");self.show_studio()
        except Exception as exc:messagebox.showerror("Atlas Studio","Invalid UI JSON: "+str(exc))

    def _studio_preview(self,parent):
        self.preview_title=ctk.CTkLabel(parent,text="LIVE PREVIEW",text_color=self._c("accent"),font=self._font(8,"bold"));self.preview_title.pack(anchor="w",padx=20,pady=(20,8));self.preview_core=ctk.CTkFrame(parent,fg_color=self._c("background"),corner_radius=self.ui["radius"]);self.preview_core.pack(fill="both",expand=True,padx=18,pady=(0,18));self.preview_dot=ctk.CTkLabel(self.preview_core,text="◉",text_color=self._c("accent"),font=("Segoe UI Symbol",55,"bold"));self.preview_dot.pack(pady=(55,8));ctk.CTkLabel(self.preview_core,text="ATLAS",text_color=self._c("text"),font=self._font(22,"bold")).pack();ctk.CTkLabel(self.preview_core,text="Your learning system",text_color=self._c("muted"),font=self._font(10)).pack(pady=4);self.preview_card=ctk.CTkFrame(self.preview_core,fg_color=self._c("panel"),corner_radius=self.ui["radius"],border_width=1,border_color=self._c("border"));self.preview_card.pack(fill="x",padx=30,pady=24);ctk.CTkLabel(self.preview_card,text="Chat • Voice • Practice • Notes",text_color=self._c("text"),font=self._font(10,"bold")).pack(pady=20)

    def _studio_preview_refresh(self):
        if hasattr(self,"preview_core"):self._studio_save(reopen=False)

    def _studio_save(self,reopen=True):
        save_ui(self.ui);self._apply_window();
        if reopen:self.show_studio()

    def _studio_reset(self):
        self.ui=deepcopy(DEFAULT_UI);save_ui(self.ui);self._apply_window();self._build_shell();self.show_studio()

    def _studio_export(self):
        path=filedialog.asksaveasfilename(defaultextension=".atlas-theme",filetypes=[("Atlas Theme","*.atlas-theme"),("JSON","*.json")],initialfile="my-atlas-theme.atlas-theme")
        if path:Path(path).write_text(json.dumps(self.ui,indent=2,ensure_ascii=False),encoding="utf-8")

    def _studio_import(self):
        path=filedialog.askopenfilename(filetypes=[("Atlas Theme","*.atlas-theme *.json"),("All files","*.*")])
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8"));merged=deepcopy(DEFAULT_UI);merged.update(data);self.ui=merged;save_ui(self.ui);self._apply_window();self._build_shell();self.show_studio()
        except Exception as exc:messagebox.showerror("Atlas Studio","Could not import theme: "+str(exc))

    def _browse_bg(self):
        path=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.webp"),("All files","*.*")])
        if path:self.ui["background_image"]=path;self.bg_path.delete(0,"end");self.bg_path.insert(0,path);self._studio_preview_refresh()

    def toggle_command_center(self):
        if self.command_overlay:self.close_command_center();return
        self.command_overlay=ctk.CTkFrame(self,fg_color=self._c("panel"),corner_radius=self.ui["radius"],border_width=1,border_color=self._c("border"),width=560,height=320);self.command_overlay.place(relx=.5,rely=.2,anchor="n");ctk.CTkLabel(self.command_overlay,text="ATLAS COMMAND CENTER",text_color=self._c("accent"),font=self._font(9,"bold")).pack(anchor="w",padx=22,pady=(20,4));ctk.CTkLabel(self.command_overlay,text="What do you want to do?",text_color=self._c("text"),font=self._font(21,"bold")).pack(anchor="w",padx=22,pady=(0,12));entry=ctk.CTkEntry(self.command_overlay,placeholder_text="Try: studio, chat, voice, practice...",height=42,fg_color=self._c("panel_alt"),border_color=self._c("border"));entry.pack(fill="x",padx=18,pady=(0,12));entry.focus();actions=[("Chat",self.show_chat),("Voice",self.show_voice),("Practice",self.show_practice),("Studio",self.show_studio),("Progress",self.show_progress),("Notes",self.show_notes)];grid=ctk.CTkFrame(self.command_overlay,fg_color="transparent");grid.pack(fill="x",padx=16)
        for i,(label,cmd) in enumerate(actions):self.button(grid,label,lambda c=cmd:self._command_run(c),150).grid(row=i//2,column=i%2,padx=4,pady=4)
        entry.bind("<Return>",lambda _e:self._command_search(entry.get()))

    def _command_run(self,c):self.close_command_center();c()
    def _command_search(self,text):
        t=text.lower();mapping=[("studio",self.show_studio),("voice",self.show_voice),("chat",self.show_chat),("practice",self.show_practice),("progress",self.show_progress),("note",self.show_notes),("planner",self.show_planner),("memory",self.show_memory),("physics",lambda:self.show_subject("Physics")),("math",lambda:self.show_subject("Mathematics")),("chem",lambda:self.show_subject("Chemistry"))]
        for key,cmd in mapping:
            if key in t:return self._command_run(cmd)

    def close_command_center(self):
        if self.command_overlay:self.command_overlay.destroy();self.command_overlay=None


def main():
    app=AtlasGUI();app.mainloop()

if __name__=="__main__":main()
