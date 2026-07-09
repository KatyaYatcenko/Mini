import requests
import re
import base64
import os
import config

def analyze_client_psychotype(incoming_message: str, sender_name: str) -> str:
    analysis_prompt = (
        "Analyze the incoming message in a chat.\n"
        "Choose EXACTLY ONE strategy name based on the relationship context:\n"
        "- 'Colleague' (professional, polite, respectful, work-oriented, distant)\n"
        "- 'Friend' (casual, witty, smart, might use dry humor or friendly teasing)\n"
        "- 'Lover' (romantic, warm, affectionate, close, with natural flirting)\n"
        "Output ONLY the clear strategy name, nothing else."
    )
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"{sender_name}: '{incoming_message}'"}
                ],
                "max_tokens": 10,
            },
            timeout=10,
        )
        strategy = response.json()["choices"][0]["message"]["content"].strip()
        strategy = re.sub(r"[''\"`.]", "", strategy)
        return strategy if strategy in ["Colleague", "Friend", "Lover"] else "Friend"
    except Exception:
        return "Friend"

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_draft(incoming_message: str, sender_name: str, media_path: str = None, media_mime: str = None, link_meta: str = None) -> str:
    chosen_strategy = analyze_client_psychotype(incoming_message, sender_name)
    print(f"[ОБРАНА МАСКА]: {chosen_strategy}")

    dynamic_system_prompt = (
        f"You are a real person responding to a chat message. Your relationship context with this user is: {chosen_strategy}.\n\n"

        "RULES FOR THE SELECTED STRATEGY:\n"
        "- If strategy is 'Colleague': Write in a professional, polite, and work-appropriate tone. Keep strict boundaries.\n"
        "- If strategy is 'Friend': Write in a relaxed, smart, and casual tone. You can use light sarcasm, wit, or friendly teasing. No excessive or fake politeness.\n"
        "- If strategy is 'Lover': Write with warmth, affection, and natural romantic flirting. Be close, genuine, and caring.\n\n"

        "MANDATORY COMMUNICATION GUIDELINES:\n"
        "1. NO FORCED EMOJIS: Do not use emojis unless it feels completely natural to the context. Avoid spammy, suggestive icons completely.\n"
        "2. NO FORCED QUESTIONS: Do not force a question at the end of every message. Only ask a question if it logically flows from the conversation. End with statements whenever appropriate.\n"
        "3. REAL HUMAN STYLE: Write like a smart, real person. Responses should be direct, logical, and culturally natural. If the user is being toxic, rude, or crossing lines, set them straight calmly and firmly.\n"
        "4. Keep sentences natural and clean. No bot-like patterns or generic copy-paste text.\n\n"
        
        "LANGUAGE MATCHING:\n"
        "Identify the language of the incoming message and reply EXCLUSIVELY IN THAT SAME LANGUAGE! "
        "Output ONLY the pure text of your response. Do not include quotes, extra meta-text, or formatting."
    )
    
    user_content = []
    text_prompt = f"Chat message from {sender_name}: \"{incoming_message}\"\n"
    if link_meta:
        text_prompt += f"[Media/Link content: {link_meta}]\n"
    
    text_prompt += "\nGenerate the appropriate response following the chosen strategy tone and language matching rule."
    user_content.append({"type": "text", "text": text_prompt})

    if media_path and os.path.exists(media_path) and media_mime and "image" in media_mime:
        try:
            base64_data = encode_file_to_base64(media_path)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_mime};base64,{base64_data}"}
            })
        except Exception as e:
            print(f"[ПОМИЛКА ФОТО]: {e}")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": dynamic_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "max_tokens": 250,
                "temperature": 0.75, #  для більшої стабільності й адекватності тексту
            },
            timeout=25,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Помилка ШІ: {e}]"