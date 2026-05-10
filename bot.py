import logging
import tempfile
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = """Ты помощник для изучения английского языка.
Отвечай на русском языке. Без звёздочек."""

def start(update: Update, context: CallbackContext):
    keyboard = [
        ["📚 Слово дня", "📖 Грамматика"],
        ["✏️ Упражнение", "💬 Полезные фразы"],
        ["🔊 Озвучить слово", "❓ Задать вопрос"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Привет! Я помогу учить английский! 🇬🇧\nВыбери раздел:", reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "🔊 Озвучить слово":
        update.message.reply_text("Напиши слово или фразу на английском!")
        context.user_data["voice"] = True
        return

    if context.user_data.get("voice"):
        context.user_data["voice"] = False
        response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(response.content)
            tmp = f.name
        with open(tmp, "rb") as audio:
            update.message.reply_audio(audio=audio)
        os.unlink(tmp)
        return

    prompts = {
        "📚 Слово дня": "Дай слово дня: слово, транскрипция, перевод, 2 примера.",
        "📖 Грамматика": "Объясни одно грамматическое правило с примерами.",
        "✏️ Упражнение": "Дай упражнение с вариантами ответов.",
        "💬 Полезные фразы": "Дай 5 полезных фраз с переводом.",
        "❓ Задать вопрос": "Напиши: Задайте ваш вопрос!",
    }

    prompt = prompts.get(text, text)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    update.message.reply_text(response.choices[0].message.content)

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()