import asyncio
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# --- MA'LUMOTLAR ---
BOT_TOKEN = "8479111656:AAGLuoapeIpQdSOp79xu652Fy2W4AacJlf0"
# --------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

if not os.path.exists('downloads'): os.makedirs('downloads')

YDL_OPTS_INFO = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

@dp.message(F.text)
async def handle_universal(message: types.Message):
    query = message.text
    wait = await message.answer("🔍 Musiqa tahlil qilinmoqda...")
    
    search_query = ""
    
    # 1-QADAM: Ssilka bo'lsa, avval uning nomini aniqlaymiz
    if query.startswith("http"):
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS_INFO) as ydl:
                info = ydl.extract_info(query, download=False)
                # Videoning sarlavhasidan keraksiz belgilarni tozalaymiz
                video_title = info.get('title', '')
                # Ssilka sarlavhasini qidiruv so'ziga aylantiramiz
                search_query = f"ytsearch5:{video_title} official audio"
        except Exception:
            await wait.edit_text("❌ Ssilkani tahlil qilib bo'lmadi.")
            return
    else:
        # Matn bo'lsa to'g'ridan-to'g'ri qidiruv
        search_query = f"ytsearch5:{query} official audio"

    # 2-QADAM: Endi 1 2 3 4 5 variantlarni chiqaramiz
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_INFO) as ydl:
            results = ydl.extract_info(search_query, download=False)
            entries = results.get('entries', [])

        if not entries:
            await wait.edit_text("😔 Hech narsa topilmadi.")
            return

        builder = InlineKeyboardBuilder()
        text = "🎵 **Siz uchun topilgan original variantlar:**\n\n"
        
        for i, entry in enumerate(entries[:5], 1):
            title = entry.get('title', 'Nomsiz')
            text += f"{i}. 🎹 {title[:50]}\n\n"
            # Har bir tugma uchun ssilkani keshga saqlaymiz
            builder.button(text=str(i), callback_data=f"final_dl:{i-1}")
            setattr(dp, f"url_{message.from_user.id}_{i-1}", entry.get('webpage_url'))

        builder.adjust(5)
        await wait.edit_text(text, reply_markup=builder.as_markup())
        except Exception as e:
        print(f"Xato: {e}")
        await wait.edit_text(f"🚀 Yangi xato: {e}")
@dp.callback_query(F.data.startswith("final_dl:"))
async def process_final_dl(call: types.CallbackQuery):
    idx = call.data.split(":")[1]
    url = getattr(dp, f"url_{call.from_user.id}_{idx}", None)
    
    await call.message.edit_text("📥 Original audio yuklanmoqda...")
    
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fn = ydl.prepare_filename(info)
            
            # Musiqa metadata ma'lumotlarini olish
            song_title = info.get('title', 'Unknown')
            song_artist = info.get('uploader', 'Unknown Artist')

        # 3-QADAM: Artist va Nomi bilan yuborish
        await call.message.answer_audio(
            types.FSInputFile(fn),
            title=song_title,
            performer=song_artist,
            caption=f"✨ Original Music: {song_title}"
        )
        if os.path.exists(fn): os.remove(fn)
    except Exception:
        await call.message.answer("❌ Yuklashda xato!")
    finally:
        await call.message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
