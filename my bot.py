import os, logging, asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

logging.basicConfig(level=logging.INFO)

TOKEN = "8479111656:AAHb8B7Bd03hyQC_ii5GzjV6yIVLSJw0PCA"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(f"Salom {m.from_user.full_name}! 👋\nQo'shiq nomini yozing yoki video ssilkasini yuboring!")

@dp.message()
async def handle_message(m: types.Message):
    if not m.text: return

    # AGAR SSILKA BO'LSA
    if "http" in m.text:
        wait = await m.answer("🔗 Ssilka aniqlandi...")
        builder = InlineKeyboardBuilder()
        builder.button(text="🎬 Video (MP4)", callback_data="down_vid")
        builder.button(text="🎵 Audio (MP3)", callback_data="down_aud")
        user_data[f"{m.from_user.id}_url"] = m.text
        await wait.edit_text("Formatni tanlang:", reply_markup=builder.as_markup())
    
    # AGAR QIDIRUV (MATN) BO'LSA
    else:
        wait = await m.answer("🔍 Qidirilmoqda...")
        query = f"ytsearch5:{m.text}"
        opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                res = ydl.extract_info(query, download=False)
                entries = res.get('entries', [])
            
            if not entries:
                return await wait.edit_text("😔 Topilmadi.")
            
            builder = InlineKeyboardBuilder()
            text = "🎵 **Topilgan qo'shiqlar:**\n\n"
            for i, entry in enumerate(entries):
                title = entry.get('title', 'Nomsiz')
                text += f"{i+1}. 🎶 {title[:55]}\n\n"
                builder.button(text=str(i+1), callback_data=f"search_{i}")
                user_data[f"{m.from_user.id}_search_{i}"] = entry.get('webpage_url')
            
            builder.adjust(5)
            await wait.edit_text(text, reply_markup=builder.as_markup())
        except Exception as e:
            await wait.edit_text(f"❌ Qidiruvda xato.")

@dp.callback_query(F.data.startswith("search_"))
async def from_search(call: types.CallbackQuery):
    idx = call.data.split("_")[1]
    url = user_data.get(f"{call.from_user.id}_search_{idx}")
    await call.message.edit_text("📥 Yuklanmoqda...")
    await perform_download(call.message, url, "aud", call.from_user.id)

@dp.callback_query(F.data.startswith("down_"))
async def from_link(call: types.CallbackQuery):
    mode = call.data.split("_")[1]
    url = user_data.get(f"{call.from_user.id}_url")
    await call.message.edit_text("📥 Jarayon boshlandi...")
    await perform_download(call.message, url, mode, call.from_user.id)

async def perform_download(message, url, mode, user_id):
    ext = "mp4" if mode == "vid" else "mp3"
    file_path = f"{user_id}_{mode}.{ext}"
    
    opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if mode == "vid" else 'bestaudio/best',
        'outtmpl': file_path,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'file').replace("/", "_")
            performer = info.get('uploader', 'Universal Bot')

        input_file = types.FSInputFile(file_path, filename=f"{title}.{ext}")
        if mode == "vid":
            await message.answer_video(video=input_file, caption=f"🎬 {title}")
        else:
            await message.answer_audio(audio=input_file, title=title, performer=performer)
        await message.delete()
    except:
        await message.edit_text("❌ Blok tufayli yuklab bo'lmadi.")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
