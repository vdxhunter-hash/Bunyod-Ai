import asyncio
import logging
import os
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from google import genai
from google.genai import types as genai_types

# Token va API kalitni to'g'ridan-to'g'ri qo'shtirnoq ichiga yozamiz:
TELEGRAM_BOT_TOKEN = "9063728538:AAFyqgTdbdW-vMg-k-a4ysyDWp4SJOg0JAg"
GEMINI_API_KEY = "AQ.Ab8RN6IkeewXgRhzrbURaytSj26joAsZXmiuwCEHAEhWsfQZAQ"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)

# /start buyrug'i
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Men sizning aqlli AI agentingizman.\n\n"
        "✨ **Imkoniyatlarim:**\n"
        "1. Istalgan savolingizga Google Search orqali javob beraman.\n"
        "2. **Rasm chizish:** 'Rasm chiz: ...' deb yozing.\n"
        "3. **Video yaratish:** 'Video yarat: ...' deb yozing."
    )

# Asosiy xabarlarni qayta ishlash
@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    text_lower = text.lower()

    # --- 1. RASM GENERATSIYASI ---
    if text_lower.startswith("rasm") or "rasm chiz" in text_lower or "chizib ber" in text_lower:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
        status_msg = await message.answer("🎨 Rasm tayyorlanmoqda, biroz kuting...")
        
        try:
            # Promptni ingliz tiliga Gemini orqali tarjima qilamiz (sifatliroq chiqishi uchun)
            tr_res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Translate this prompt into a detailed English image prompt: {text}"
            )
            prompt_en = tr_res.text.strip()
            encoded_prompt = urllib.parse.quote(prompt_en)
            
            # Pollinations.ai bepul rasm URL'i
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            await message.answer_photo(
                photo=image_url,
                caption=f"🎨 **Rasm tayyor!**\n\n📌 So'rov: *{text}*"
            )
            await status_msg.delete()
        except Exception as e:
            logging.error(f"Rasm xatosi: {e}")
            await status_msg.edit_text("❌ Kechirasiz, rasmni generatsiya qilishda xatolik yuz berdi.")
        return

    # --- 2. VIDEO GENERATSIYASI ---
    if text_lower.startswith("video") or "video yarat" in text_lower or "video qil" in text_lower:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)
        status_msg = await message.answer("🎬 Video generatsiya qilinmoqda (bu 10-20 soniya vaqt olishi mumkin)...")
        
        try:
            tr_res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Translate this prompt into an English video generation prompt: {text}"
            )
            prompt_en = tr_res.text.strip()
            encoded_prompt = urllib.parse.quote(prompt_en)
            
            # Pollinations Video API (video mp4 qilib beradi)
            video_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=video"
            
            # Videoni yuklab olib, bot orqali fayl qilib yuboramiz
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as resp:
                    if resp.status == 200:
                        video_bytes = await resp.read()
                        video_file = types.BufferedInputFile(video_bytes, filename="generated_video.mp4")
                        
                        await message.answer_video(
                            video=video_file,
                            caption=f"🎬 **Video tayyor!**\n\n📌 So'rov: *{text}*"
                        )
                        await status_msg.delete()
                    else:
                        await status_msg.edit_text("❌ Video tayyorlashda xatolik yuz berdi. Qayta urinib ko'ring.")
        except Exception as e:
            logging.error(f"Video xatosi: {e}")
            await status_msg.edit_text("❌ Kechirasiz, videoni generatsiya qilishda xatolik yuz berdi.")
        return

    # --- 3. MATN VA GOOGLE SEARCH ---
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Sen o'zbek tilida muloqot qiluvchi va barcha savollarga aniq, to'liq va tushunarli javob beruvchi aqlli AI agentisan. Savol: {text}",
            config=genai_types.GenerateContentConfig(
                tools=[{"google_search": {}}],  # Google Search integratsiyasi
                temperature=0.7,
            )
        )
        
        await message.answer(response.text)
        
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        await message.answer("Kechirasiz, so'rovingizni qayta ishlashda xatolik yuz berdi.")

async def main():
    print("🚀 AI Agent Telegram Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
