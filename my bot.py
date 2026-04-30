import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot sozlamalari (Railway Variables bo'limidan oladi)
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(f"Salom {message.from_user.full_name}! 👋\n\nMenga Instagram ssilkasi yoki qo'shiq nomini yozib yuboring, men sizga original variantlarni topib beraman!")

@dp.message()
async def universal_handler(message: types.Message):
    if not message.text:
        return

    wait = await message.answer("🔍 Qidirilmoqda, kuting...")
    
    # Ssilka yoki matn ekanligini aniqlash
    if "instagram.com" in message.text or "youtube.com" in message.text or "youtu.be" in message.text:
        search_query = message.text
    else:
        # Matn bo'lsa, YouTube'dan eng sifatli audiolarni qidiradi
        search_query = f"ytsearch5:{message.text} audio"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(search_query, download=False)
            
            if 'entries' in results:
                entries = [e for e in results['entries'] if e is not None]
            else:
                entries = [results]

        if not entries:
            await wait.edit_text("😔 Hech narsa topilmadi. Iltimos, nomni aniqroq yozing yoki ssilkani tekshiring.")
            return

        builder = InlineKeyboardBuilder()
        text = "🎵 **Siz uchun topilgan original variantlar:**\n\n"
        
        for i, entry in enumerate(entries[:5], 1):
            title = entry.get('title', 'Nomsiz')
            # Natijalarni ro'yxat qilib chiqarish
            text += f"{i}. 🎶 {title[:60]}...\n\n"
            builder.button(text=str(i), callback_data=f"final_dl:{i-1}")
            # Ma'lumotlarni vaqtincha saqlash
            setattr(dp, f"url_{message.from_user.id}_{i-1}", entry.get('webpage_url'))
            
        builder.adjust(5)
        await wait.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        await wait.edit_text(f"🚀 Xatolik yuz berdi. Iltimos, birozdan so'ng qayta urining.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
