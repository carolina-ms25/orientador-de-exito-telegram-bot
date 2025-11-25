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
    import re
    from langchain_core.messages import ToolMessage
    
    last_message = response["messages"][-1]
    content = last_message.content
    response_type = response["response_type"]

    if response_type == "text":
        # Convert Markdown to HTML for Telegram
        def markdown_to_html(text):
            # Bold: **text** -> <b>text</b>
            text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
            # Italic: *text* -> <i>text</i>
            text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<i>\1</i>', text)
            return text
        
        # Extract image URL from tool messages metadata
        image_url = None
        for msg in response["messages"]:
            if isinstance(msg, ToolMessage):
                # Tool was used, check if it has metadata with image
                try:
                    # The tool returns documents, check if content has metadata markers
                    if hasattr(msg, 'artifact') and msg.artifact:
                        # Check documents in artifact
                        for doc in msg.artifact:
                            if hasattr(doc, 'metadata') and 'image_url' in doc.metadata:
                                image_url = doc.metadata['image_url']
                                break
                except:
                    pass
                break
        
        # Clean content: remove image URLs that might appear in text
        text_part = content
        text_part = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text_part)  # Remove markdown images
        text_part = re.sub(r'\[IMAGE_URL:[^\]]+\]', '', text_part)  # Remove [IMAGE_URL:...]
        text_part = re.sub(r'https://drive\.google\.com[^\s\)\]]+', '', text_part)  # Remove Drive URLs
        text_part = re.sub(r'Imagen:.*?https://[^\s]+', '', text_part)  # Remove "Imagen: url" lines
        text_part = text_part.strip()
        
        # Convert Markdown to HTML
        text_part = markdown_to_html(text_part)
        
        # Send with image if URL found from tool metadata
        if image_url:
            try:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=text_part,
                    parse_mode='HTML'
                )
            except Exception as e:
                # If image fails, send text only
                await update.message.reply_text(text_part, parse_mode='HTML')
        else:
            await update.message.reply_text(text_part, parse_mode='HTML')

    elif response_type == "audio":
        audio_bytes = response.get("audio_buffer")
        if audio_bytes:
            await update.message.reply_voice(voice=audio_bytes)

    else:
        await update.message.reply_text("Sorry, I can't talk right now buddy! 😔")
