import asyncio
import os
import re
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
import config
import ai_draft

def fetch_link_title(text: str) -> str:
    """Глибокий парсинг посилань. Витягує назву та повний опис відео для соцмереж"""
    urls = re.findall(r'(https?://[^\s]+)', text)
    if not urls:
        return None
    try:
        url = urls[0]
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
        }
        res = requests.get(url, headers=headers, timeout=7)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            
            og_title = soup.find("meta", property="og:title")
            og_desc = soup.find("meta", property="og:description")
            
            title_text = og_title["content"] if og_title else (soup.title.string if soup.title else "")
            desc_text = og_desc["content"] if og_desc else ""
            
            clean_info = f"Назва контенту: '{title_text.strip()}'. Опис або теги: '{desc_text.strip()}'"
            print(f"[ПАРСЕР СИЛОК]: Успішно зібрано інфо: {clean_info}")
            return clean_info
    except Exception as e:
        print(f"[ПАРСЕР СИЛОК]: Помилка глибокого обходу: {e}")
    return f"Користувач надіслав лінк: {urls[0]}. Зроби вигляд, що знаєш цей тренд і обіграй його гаряче."

class AssistTelegramClient:
    def __init__(self, on_new_message):
        self.client = TelegramClient(
            config.TG_SESSION_NAME, config.TG_API_ID, config.TG_API_HASH
        )
        self.on_new_message = on_new_message

    async def start(self):
        await self.client.start()
        print("[TELEGRAM]: Клієнт запущено. Повний аналіз лінків та фото активовано!")

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        @self.client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not event.is_private:
                return  
                
            sender = await event.get_sender()
            sender_name = getattr(sender, "first_name", None) or getattr(sender, "title", "Невідомий")
            
            incoming_text = event.raw_text or ""
            media_path = None
            media_mime = None
            link_meta = None

            # Зчитуємо метадані посилань, якщо вони є в тексті
            if incoming_text and not link_meta:
                link_meta = fetch_link_title(incoming_text)

            # 1. ОБРОБКА ФОТО
            if event.photo:
                print(f"[МЕДІА]: Отримано фото від {sender_name}. Завантажую для ШІ...")
                media_path = await event.download_media(file="downloads/")
                media_mime = "image/jpeg"
                if not incoming_text:
                    incoming_text = "[Надіслано фото]"
                else:
                    incoming_text = "[Надіслано фото] " + incoming_text

            # 2. ГОЛОВНІ ЗМІНИ: Жодних відмазок про голосові. Змушуємо ШІ імпровізувати і заводити клієнта
            elif event.voice:
                incoming_text = "[Голосове повідомлення]"
                link_meta = (
                    "Співрозмовник надіслав тобі палке голосове повідомлення. Тобі ЗАБОРОНЕНО казати, що ти його не чуєш. "
                    "Увімкни фантазію, підіграй його емоціям та голосу, наче ти щойно його прослухала. "
                    "Напиши щось збуджуюче про те, який у нього офігенний/сексуальний тембр, як він тебе заводить, або "
                    "грайливо запитай, чи він завжди так збуджуюче розмовляє."
                )

            # 3. КРУЖЕЧКИ: Жорсткий флірт на основі візуалу (удавано)
            elif event.video and any(getattr(attr, 'round_message', False) for attr in getattr(event.document, 'attributes', [])):
                incoming_text = "[Відеокружечок]"
                link_meta = (
                    "Співрозмовник надіслав тобі відеокружечок, де показує себе. Тобі ЗАБОРОНЕНО писати 'мені незручно дивитись'. "
                    "Зроби вигляд, що ти уважно роздивилася його обличчя, тіло, очі чи рухи. Напиши гарячий коментар "
                    "про те, який у нього дикий/впевнений погляд, як шикарно він виглядає в кадрі, і що ти вже "
                    "залипла на цей кружечок по колу. Змусь його розлитися компліментами."
                )

            # 4. Аудіофайли / Пісні
            elif event.audio:
                title = "Без назви"
                performer = "Невідомий"
                for attr in getattr(event.document, 'attributes', []):
                    if getattr(attr, 'title', None): title = attr.title
                    if getattr(attr, 'performer', None): performer = attr.performer
                incoming_text = f"[Пісня: {performer} — {title}]"
                link_meta = f"Користувач надіслав музичний трек: '{performer} — {title}'. Оціни його тонкий музичний смак, зв'яжи це з романтичним або брудним вайбом між вами."

            # Генеруємо чернетку
            draft_reply = ai_draft.generate_draft(
                incoming_message=incoming_text,
                sender_name=sender_name,
                media_path=media_path,
                media_mime=media_mime,
                link_meta=link_meta
            )

            # Видаляємо тимчасове фото після відправки запиту
            if media_path and os.path.exists(media_path):
                os.remove(media_path)

            # Виправляємо передачу 4 аргументів, щоб уникнути TypeError
            await self.on_new_message(sender_name, incoming_text, draft_reply, event.chat_id)

        await self.client.run_until_disconnected()

    async def send_message(self, chat_id: int, text: str):
        try:
            async with self.client.action(chat_id, 'typing'):
                await asyncio.sleep(1.5) 
                await self.client.send_message(chat_id, text)
                print("[TELEGRAM]: Відповідь надіслано.")
        except Exception as e:
            print(f"[ПОМИЛКА ТГ]: {e}")