import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# Bot tokenini shu yerga yozing yoki Railway Variables'dan oladi
TOKEN = "8479111656:AAGLuoapeIpQdSOp79xu652Fy2W4AacJlf0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom Yukari! Menga Instagram ssilkasini yuboring, men uni yuklab beraman.")

@dp.message(F.text.contains("instagram.com"))
async def insta_handler(message: types.Message):
    wait = await message.answer("🔍 Qidirilmoqda, kuting...")
ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        },
    }
try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(message.text, download=False)
            entries = results.get('entries', [])

        if not entries:
            await wait.edit_text("😔 Hech narsa topilmadi.")
            return

        builder = InlineKeyboardBuilder()
        text = "🎵 **Siz uchun topilgan original variantlar:**\n\n"
        
        for i, entry in enumerate(entries[:5], 1):
            title = entry.get('title', 'Nomsiz')
            text += f"{i}. 🎬 {title[:50]}\n\n"
            # Har bir tugma uchun ssilkani keshga saqlaymiz
            builder.button(text=str(i), callback_data=f"final_dl:{i-1}")
            setattr(dp, f"url_{message.from_user.id}_{i-1}", entry.get('webpage_url'))
            
        builder.adjust(5)
        await wait.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        print(f"Xato: {e}")
        await wait.edit_text(f"🚀 Xatolik yuz berdi: {e}")

@dp.callback_query(F.data.startswith("final_dl:"))
async def process_final_dl(call: types.CallbackQuery):
    idx = call.data.split(":")[1]
    url = getattr(dp, f"url_{call.from_user.id}_{idx}", None)

    if not url:
        await call.answer("❌ Ssilka muddati tugagan.", show_alert=True)
        return

    await call.message.edit_text("⌛ Audio yuklanmoqda, kuting...")

    opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fn = ydl.prepare_filename(info)
            
            audio = types.FSInputFile(fn)
            await call.message.answer_audio(audio, caption="✅ Tayyor!")
            
            # Faylni o'chirish
            if os.path.exists(fn):
                os.remove(fn)
                
    except Exception as e:
        await call.message.answer(f"❌ Yuklashda xato: {e}")

async def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
