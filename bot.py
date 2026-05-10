import logging
import tempfile
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Твои ключи
import os
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = """Ты — помощник для изучения английского языка.
Отвечай на русском языке, если не просят иначе.
Помогай с грамматикой, лексикой, упражнениями и полезными фразами.
Давай примеры использования слов и фраз.
Не используй markdown форматирование со звёздочками."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📚 Слово дня", "📖 Грамматика"],
        ["✏️ Упражнение", "💬 Полезные фразы"],
        ["🔊 Озвучить слово", "❓ Задать вопрос"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я помогу тебе учить английский! 🇬🇧\nВыбери раздел:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🔊 Озвучить слово":
        await update.message.reply_text("Напиши слово или фразу на английском, и я её озвучу!")
        context.user_data["waiting_for_voice"] = True
        return

    if context.user_data.get("waiting_for_voice"):
        context.user_data["waiting_for_voice"] = False
        await send_voice(update, text)
        return

    prompts = {
        "📚 Слово дня": "Дай мне слово дня на английском. Напиши слово, транскрипцию, перевод, и 2 примера предложений. Без звёздочек.",
        "📖 Грамматика": "Объясни одно грамматическое правило английского языка с примерами. Без звёздочек.",
        "✏️ Упражнение": "Дай небольшое упражнение по английскому языку с вариантами ответов. Без звёздочек.",
        "💬 Полезные фразы": "Дай 5 полезных разговорных фраз на английском с переводом. Без звёздочек.",
        "❓ Задать вопрос": "Напиши: Задайте ваш вопрос по английскому языку!",
    }

    user_prompt = prompts.get(text, text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    answer = response.choices[0].message.content
    await update.message.reply_text(answer)

async def send_voice(update: Update, word: str):
    await update.message.reply_text(f"Озвучиваю: {word} 🔊")
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=word
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(response.content)
        tmp_path = f.name
    with open(tmp_path, "rb") as audio:
        await update.message.reply_audio(audio=audio)
    os.unlink(tmp_path)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()