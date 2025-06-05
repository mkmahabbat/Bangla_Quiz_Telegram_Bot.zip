import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
import random

TOKEN = "7685067743:AAGJ77HmwGProGGHmw6X1-l3RZK8Lw_Aagw"

SUBJECTS = ["geography", "math", "history", "physical_science", "life_science"]
QUIZ_DATA = {subject: json.load(open(f"questions/{subject}.json", "r", encoding="utf-8")) for subject in SUBJECTS}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

SELECTING_SUBJECT, ASKING_QUESTION = range(2)

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[s] for s in SUBJECTS]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("আপনি কোন বিষয় থেকে কুইজ দিতে চান?", reply_markup=reply_markup)
    return SELECTING_SUBJECT

async def select_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    if subject not in SUBJECTS:
        await update.message.reply_text("দয়া করে তালিকা থেকে একটি বিষয় নির্বাচন করুন।")
        return SELECTING_SUBJECT

    questions = QUIZ_DATA[subject]
    user_sessions[update.effective_user.id] = {
        "subject": subject,
        "questions": random.sample(questions, 5),
        "current": 0,
        "score": 0
    }
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = user_sessions[update.effective_user.id]
    if session["current"] >= len(session["questions"]):
        await update.message.reply_text(f"আপনার স্কোর: {session['score']} / {len(session['questions'])}")
        return ConversationHandler.END

    q = session["questions"][session["current"]]
    options = q["options"]
    context.user_data["correct_answer"] = q["answer"]
    reply_markup = ReplyKeyboardMarkup([[opt] for opt in options], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"{session['current'] + 1}. {q['question']}", reply_markup=reply_markup)
    return ASKING_QUESTION

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    correct = context.user_data["correct_answer"]
    if user_answer == correct:
        await update.message.reply_text("✅ সঠিক উত্তর!")
        user_sessions[update.effective_user.id]["score"] += 1
    else:
        await update.message.reply_text(f"❌ ভুল উত্তর। সঠিক উত্তর ছিল: {correct}")
    user_sessions[update.effective_user.id]["current"] += 1
    return await ask_question(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("কুইজ বাতিল করা হয়েছে।")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_subject)],
            ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.run_polling()
