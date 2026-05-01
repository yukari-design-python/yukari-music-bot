import os, logging, asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

logging.basicConfig(level=logging.INFO)

TOKEN = "8479111656:AAHZ306sKkuA3BuLELinEaZVun7iYQUBHZ8"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(
        f"Salom {m.from_user.full_name}! 👋\n\n"
        "Men har qanday platformadan (TikTok, Insta, Pinterest va b.) "
        "video va musiqalarni yuklab beraman. Ssilka yuboring!"
    )

@dp.message()
async def handle_message(m: types.Message):
    if not m.text or "http" not in m.text:
        return await m.answer("Iltimos, video yoki musiqa ssilkasini yuboring!")

    wait = await m.answer("🔎 Ssilka tahlil qilinmoqda...")
    url = m.text
    
    # Format tanlash tugmalari
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Video (MP4)", callback_data="down_vid")
    builder.button(text="🎵 Audio (MP3)", callback_data="down_aud")
    
    user_data[f"{m.from_user.id}_url"] = url
    await wait.edit_text("Qaysi formatda yuklamoqchisiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("down_"))
async def process_download(call: types.CallbackQuery):
    mode = call.data.split("_")[1]
    url = user_data.get(f"{call.from_user.id}_url")
    
    if not url:
        return await call.answer("Xatolik! Ssilkani qaytadan yuboring.", show_alert=True)
    
    await call.message.edit_text("📥 Yuklanmoqda... (Katta videolar biroz vaqt olishi mumkin)")
    
    ext = "mp4" if mode == "vid" else "mp3"
    file_path = f"{call.from_user.id}_{mode}.{ext}"
    
    # YouTube blokidan qochish va boshqa saytlar uchun eng kuchli sozlamalar
    opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if mode == "vid" else 'bestaudio/best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'add_header': [
            'Accept-Language: en-US,en;q=0.9',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ]
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'file').replace("/", "_")

        input_file = types.FSInputFile(file_path, filename=f"{title}.{ext}")
        
        if mode == "vid":
            await call.message.answer_video(video=input_file, caption=f"✅ {title}")
        else:
            await call.message.answer_audio(audio=input_file, title=title)
            
        await call.message.delete()
    except Exception as e:
        logging.error(f"Xato: {e}")
        await call.message.edit_text("❌ Kechirasiz, ushbu ssilkani yuklab bo'lmadi. Saytda cheklov bo'lishi mumkin.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
