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
    await m.answer(f"Salom {m.from_user.full_name}! 👋\nSsilka yuboring yoki qo'shiq nomini yozing!")

@dp.message()
async def search(m: types.Message):
    if not m.text: return
    wait = await m.answer("🔍 Qidirilmoqda...")
    query = m.text if "http" in m.text else f"ytsearch5:{m.text} audio"
    
    opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(query, download=False)
            entries = res.get('entries', [res]) if 'entries' in res or 'url' in res else []
        if not entries:
            return await wait.edit_text("😔 Topilmadi.")
        
        builder = InlineKeyboardBuilder()
        text = "🎵 **Topilgan variantlar:**\n\n"
        for i, entry in enumerate(entries[:5]):
            url = entry.get('webpage_url') or entry.get('url')
            title = entry.get('title', 'Nomsiz')
            text += f"{i+1}. 🎶 {title[:50]}\n\n"
            builder.button(text=str(i+1), callback_data=f"dl_{i}")
            user_data[f"{m.from_user.id}_{i}"] = url
        builder.adjust(5)
        await wait.edit_text(text, reply_markup=builder.as_markup())
    except Exception as e:
        await wait.edit_text(f"❌ Xato: {e}")

@dp.callback_query(F.data.startswith("dl_"))
async def download(call: types.CallbackQuery):
    idx = call.data.split("_")[1]
    url = user_data.get(f"{call.from_user.id}_{idx}")
    if not url: return await call.answer("Xatolik!", show_alert=True)
    await call.message.edit_text("📥 Yuklanmoqda...")
    
    # Qo'shiq nomini olish
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'music')
    except:
        title = "music"

    file_path = f"{call.from_user.id}.m4a"   
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        audio = types.FSInputFile(file_path, filename=f"{title}.m4a")
        await call.message.answer_audio(audio=audio, title=title)
        
        await call.message.delete()
        if os.path.exists(file_path): os.remove(file_path)
