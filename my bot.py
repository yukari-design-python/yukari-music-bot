import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Token muhit o'zgaruvchisidan olinadi
TOKEN = os.getenv("BOT_TOKEN", "8479111656:AAHZ306sKkuA3BuLELinEaZVun7iYQUBHZ8")
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(
        f"Salom {m.from_user.full_name}! 👋\n\n"
        "🎵 Men YouTube'dan musiqa yuklab beruvchi botman.\n\n"
        "📝 Ssilka yuboring yoki qo'shiq nomini yozing!"
    )

@dp.message()
async def search(m: types.Message):
    if not m.text: 
        return
    
    # Kanal yoki guruh postlarida ishlamasin
    if m.chat.type != 'private':
        return

    wait = await m.answer("🔍 Qidirilmoqda...")
    
    # URL aniqlash
    if "youtube.com" in m.text or "youtu.be" in m.text:
        query = m.text
        is_search = False
    else:
        query = f"ytsearch5:{m.text}"
        is_search = True
    
    opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': is_search,  # Qidiruvda tezroq
        'force_generic_extractor': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(query, download=False)
            
            if is_search:
                entries = res.get('entries', [])
            else:
                entries = [res] if res else []
        
        if not entries:
            await wait.delete()
            await m.answer("😔 Hech narsa topilmadi. Qayta urinib ko'ring.")
            return
        
        builder = InlineKeyboardBuilder()
        text = f"🎵 **{len(entries[:5])} ta variant topildi:**\n\n"
        
        for i, entry in enumerate(entries[:5]):
            url = entry.get('webpage_url') or entry.get('url')
            title = entry.get('title', 'Nomsiz')
            duration = entry.get('duration', 0)
            
            # Davomiylikni formatlash
            mins, secs = divmod(duration or 0, 60)
            duration_str = f"{mins}:{secs:02d}" if duration else "Noma'lum"
            
            text += f"{i+1}. 🎶 {title[:60]}\n"
            text += f"   ⏱ {duration_str}\n\n"
            
            builder.button(text=str(i+1), callback_data=f"dl_{i}")
            user_data[f"{m.from_user.id}_{i}"] = url
            
        builder.button(text="❌ Bekor qilish", callback_data="cancel")
        builder.adjust(5, 1)
        
        await wait.edit_text(
            text, 
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except yt_dlp.utils.DownloadError as e:
        await wait.edit_text(f"❌ Youtube xatosi: {str(e)[:100]}")
    except Exception as e:
        logging.error(f"Search error: {e}")
        await wait.edit_text("😕 Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")

@dp.callback_query(F.data == "cancel")
async def cancel_search(call: types.CallbackQuery):
    user_data.clear()
    await call.message.delete()
    await call.answer("Bekor qilindi ✅")

@dp.callback_query(F.data.startswith("dl_"))
async def download(call: types.CallbackQuery):
    idx = call.data.split("_")[1]
    url = user_data.get(f"{call.from_user.id}_{idx}")
    
    if not url:
        return await call.answer("⚠️ Bu qo'shiq eskirgan!", show_alert=True)
    
    await call.message.edit_text("📥 Yuklanmoqda... Iltimos kuting.")
    
    file_path = f"temp_{call.from_user.id}_{idx}.m4a"
    
    opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
    }
    
    try:
        # Ma'lumot olish
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'music')
            # Fayl nomi uchun tozalash
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Yuklash
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        # Faylni tekshirish
        if not os.path.exists(file_path):
            raise FileNotFoundError("Fayl topilmadi")
        
        # Audio yuborish
        audio = types.FSInputFile(file_path, filename=f"{title}.m4a")
        await call.message.answer_audio(
            audio=audio,
            title=title,
            performer="YouTube",
        )
        await call.message.delete()
        
    except Exception as e:
        logging.error(f"Download error: {e}")
        await call.message.edit_text(
            "❌ Yuklashda xatolik! Bu quyidagi sabablarga ko'ra bo'lishi mumkin:\n"
            "• Video mavjud emas\n"
            "• Cheklovlar mavjud\n"
            "• Yuklash hajmi juda katta (50MB dan oshiq)\n\n"
            "Iltimos, boshqa qo'shiq tanlang."
        )
    finally:
        # Faylni o'chirish
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        # Cachedan tozalash
        for key in list(user_data.keys()):
            if key.startswith(str(call.from_user.id)):
                del user_data[key]

async def main():
    logging.info("Bot ishga tushdi...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot to'xtadi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
