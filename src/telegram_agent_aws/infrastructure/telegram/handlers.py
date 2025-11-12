import os

from telegram import Update
from telegram.ext import ContextTypes

from telegram_agent_aws.application.conversation_service.generate_response import get_agent_response
from telegram_agent_aws.infrastructure.clients.elevenlabs import get_elevenlabs_client
from telegram_agent_aws.infrastructure.clients.openai import get_openai_client

openai_client = get_openai_client()
elevenlabs_client = get_elevenlabs_client()


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = get_agent_response({"messages": user_message, "input_type": "text"}, user_id=update.message.from_user.id)

    await send_response(update, context, response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    file_path = "/tmp/voice.ogg"
    await file.download_to_drive(file_path)

    with open(file_path, "rb") as audio_file:
        transcription = openai_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
        )
    os.remove(file_path)

    response = get_agent_response({"messages": transcription.text, "input_type": "voice"}, user_id=update.message.from_user.id)

    await send_response(update, context, response)



async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response: dict):
    last_message = response["messages"][-1]
    content = last_message.content
    response_type = response["response_type"]

    if response_type == "text":
        await update.message.reply_text(content)

    elif response_type == "audio":
        audio_bytes = response.get("audio_buffer")
        if audio_bytes:
            await update.message.reply_voice(voice=audio_bytes)

    else:
        await update.message.reply_text("Sorry, I can't talk right now buddy! 😔")
