import asyncio
import queue
import threading
import time
import random
import keyboard  
import pyperclip  # прописати: pip install pyperclip

import config
import ai_draft
import ui_window

incoming_queue = queue.Queue()
tg_loop = None
tg_client_wrapper = None

def add_human_typos(text: str) -> str:
    words = text.split()
    corrupted_words = []
    for word in words:
        if len(word) > 3 and random.random() < 0.08:
            idx = random.randint(1, len(word) - 2)
            word = word[:idx] + word[idx+1] + word[idx] + word[idx+2:]
        corrupted_words.append(word)
    return " ".join(corrupted_words)

def setup_hotkeys():
    def on_wakeup():
        if not ui_window.IS_ACTIVE:
            ui_window.IS_ACTIVE = True
            print("\n🔔 [СИСТЕМА]: ❤️ Комбінація B+K спрацювала! Бот ПРОКИНУВСЯ і знову працює.")
    keyboard.add_hotkey("b+k", on_wakeup)

def start_telegram_thread():
    global tg_loop, tg_client_wrapper
    from telegram_client import AssistTelegramClient

    def run():
        global tg_loop, tg_client_wrapper
        tg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(tg_loop)

        async def on_new_message(sender_name, incoming_text, draft_reply, chat_id):
            # Передаємо False наприкінці, бо це НЕ буфер обміну
            incoming_queue.put((sender_name, incoming_text, draft_reply, chat_id, False))

        tg_client_wrapper = AssistTelegramClient(on_new_message)
        tg_loop.run_until_complete(tg_client_wrapper.start())

    threading.Thread(target=run, daemon=True).start()

# --- НОВИЙ ПОТІК ДЛЯ МОНІТОРИНГУ БУФЕРА ОБМІНУ ---
def start_clipboard_thread():
    def run():
        print("[СИСТЕМА]: Моніторинг буфера обміну (Ctrl+C) активовано!")
        last_clipboard_text = ""
        while True:
            try:
                current_text = pyperclip.paste()
                if current_text:
                    current_text = current_text.strip()
                
                # Якщо з'явився новий текст, якого не було раніше
                if current_text and current_text != last_clipboard_text:
                    # Захист: ігноруємо системні мітки ТГ, щоб не зациклювати софт
                    if not current_text.startswith("[Надіслано фото]") and "[Пісня:" not in current_text:
                        print(f"[БУФЕР]: Зловлено текст: '{current_text[:30]}...'")
                        last_clipboard_text = current_text
                        
                        # Миттєво генеруємо чернетку під вайб
                        draft_reply = ai_draft.generate_draft(
                            incoming_message=current_text,
                            sender_name="Клієнт з Браузера",
                            link_meta=None
                        )
                        
                        # Кидаємо в чергу. Замість chat_id пишемо "CLIPBOARD", а True означає — це буфер обміну!
                        incoming_queue.put(("WhatsApp / OnlyFans", current_text, draft_reply, "CLIPBOARD", True))
            except Exception as e:
                print(f"[ПОМИЛКА БУФЕРА]: {e}")
            
            time.sleep(1.0)  # Перевірка раз на секунду

    threading.Thread(target=run, daemon=True).start()

def send_via_telegram(chat_id: int, text: str):
    if tg_loop is None or tg_client_wrapper is None:
        return
    asyncio.run_coroutine_threadsafe(
        tg_client_wrapper.send_message(chat_id, text), tg_loop
    )

def poll_queue(app: ui_window.App):
    try:
        while True:
            # Тепер дістаємо 5 параметрів із черги
            sender_name, incoming_text, draft_reply, chat_id, is_clipboard_mode = incoming_queue.get_nowait()
            if ui_window.IS_ACTIVE:
                handle_new_message(app, sender_name, incoming_text, draft_reply, chat_id, is_clipboard_mode)
            else:
                print(f"[РЕЖИМ СНУ]: Пропущено повідомлення від {sender_name}")
    except queue.Empty:
        pass
    app.root.after(300, poll_queue, app)

def handle_approved_action(chat_id, final_text, is_clipboard_mode):
    def process():
        human_text = add_human_typos(final_text)
        typing_speed = len(human_text) * 0.05
        total_delay = typing_speed + random.uniform(0.5, 1.5)
        
        print(f"[АВТОПІЛОТ]: Імітую введення тексту {total_delay:.1f} сек...")
        time.sleep(total_delay)
        
        if is_clipboard_mode:
            # ЯКЩО ЦЕ БУФЕР: Закидуємо фінальний текст назад, щоб просто натиснути Ctrl+V
            pyperclip.copy(human_text)
            print("[АВТОПІЛОТ]: Текст скопійовано! Переходь у WhatsApp та тисни Ctrl+V.")
        else:
            # ЯКЩО ЦЕ ТЕЛЕГРАМ: кидаємо в чат як зазвичай
            send_via_telegram(chat_id, human_text)
            
    threading.Thread(target=process, daemon=True).start()

def handle_new_message(app: ui_window.App, sender_name, incoming_text, draft_reply, chat_id, is_clipboard_mode):
    def show():
        # Додаємо підтримку нового аргументу is_clipboard_mode у вікно
        app.show_decision_window(
            sender_name, incoming_text, draft_reply,
            on_approve=lambda final_text: handle_approved_action(chat_id, final_text, is_clipboard_mode),
            on_sleep=lambda: print("[СИСТЕМА]: Бот тимчасово вимкнено користувачем."),
            is_clipboard_mode=is_clipboard_mode  # Передаємо прапорець у твоє GUI вікно
        )
    app.root.after(0, show)

def main():
    start_telegram_thread()
    start_clipboard_thread()  # Запускаємо наш новий фоновий моніторинг буфера
    setup_hotkeys()

    app = ui_window.App()
    app.root.after(300, poll_queue, app)
    print("[СИСТЕМА]: Сервіс успішно запущено. Очікую контент...")
    app.run()

if __name__ == "__main__":
    main()