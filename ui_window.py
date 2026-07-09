import tkinter as tk
from tkinter import font as tkfont
import pyperclip  # Робота з буфером обміну

IS_ACTIVE = True 

class DraftWindow:
    def __init__(self, root, sender_name, incoming_text, draft_text, on_approve, on_sleep, is_clipboard_mode=False):
        self.root = root
        self.on_approve = on_approve
        self.on_sleep = on_sleep
        self.is_clipboard_mode = is_clipboard_mode

        self.win = tk.Toplevel(root)
        self.win.title(f"Контроль діалогу: {sender_name}")
        self.win.geometry("580x450")
        self.win.attributes("-topmost", True)

        big_font = tkfont.Font(size=14)
        btn_font = tkfont.Font(size=14, weight="bold")

        # Адаптуємо заголовок під джерело тексту
        title_text = f"Зловлено з буфера ({sender_name}):" if is_clipboard_mode else f"Отримано від {sender_name}:"

        tk.Label(
            self.win, text=title_text,
            font=tkfont.Font(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=15, pady=(15, 2))

        tk.Label(
            self.win, text=incoming_text, font=big_font, fg="#333",
            anchor="w", justify="left", wraplength=540, bg="#f5f5f5", padx=10, pady=10
        ).pack(fill="x", padx=15, pady=(0, 15))

        tk.Label(
            self.win, text="Текст відповіді (можна редагувати прямо тут):",
            font=tkfont.Font(size=12, weight="bold"), anchor="w"
        ).pack(fill="x", padx=15)

        self.text_box = tk.Text(self.win, height=6, font=big_font, wrap="word")
        self.text_box.insert("1.0", draft_text)
        self.text_box.pack(fill="both", expand=True, padx=15, pady=5)

        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=15, pady=20)

        # Динамічний текст на зеленій кнопці
        approve_btn_text = "📋 СКОПІЮВАТИ В БУФЕР" if is_clipboard_mode else "🚀 УХВАЛИТИ ТА ВІДПРАВИТИ"

        approve_btn = tk.Button(
            btn_frame, text=approve_btn_text, font=btn_font,
            bg="#2e7d32", fg="white", height=2, command=self._click_approve
        )
        approve_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        sleep_btn = tk.Button(
            btn_frame, text="😴 НІ, Я САМА (Заснути)", font=btn_font,
            bg="#c62828", fg="white", height=2, command=self._click_sleep
        )
        sleep_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.win.protocol("WM_DELETE_WINDOW", self._click_sleep)

    def _click_approve(self):
        final_text = self.text_box.get("1.0", "end").strip()
        
        # Якщо активовано режим буфера — миттєво перезаписуємо буфер обміну фінальним текстом
        if self.is_clipboard_mode:
            pyperclip.copy(final_text)
            print("[UI]: Текст скопійовано назад у буфер обміну. Можна тицяти Ctrl+V в чаті.")

        self.on_approve(final_text)
        self.win.destroy()

    def _click_sleep(self):
        global IS_ACTIVE
        IS_ACTIVE = False
        print("\n💤 [СИСТЕМА]: Бот переведено в режим СНУ. Очікування комбінації B+K...")
        self.on_sleep()
        self.win.destroy()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def show_decision_window(self, sender_name, incoming_text, draft_text, on_approve, on_sleep, is_clipboard_mode=False):
        global IS_ACTIVE
        if not IS_ACTIVE:
            return
        
        # Виклик через .after(0, ...) гарантує, що вікно відкриється в головному потоці
        # і додаток не зависне через фоновий потік моніторингу буфера
        self.root.after(0, lambda: DraftWindow(
            self.root, sender_name, incoming_text, draft_text, on_approve, on_sleep, is_clipboard_mode
        ))

    def run(self):
        self.root.mainloop()