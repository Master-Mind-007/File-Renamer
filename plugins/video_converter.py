
# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import random
import time

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config


from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)


from helper_funcs.display_progress import progress_for_pyrogram
from helper_funcs.help_Nekmo_ffmpeg import take_screen_shot

from pyrogram.types import InlineKeyboardButton
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, UserBannedInChannel 

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from PIL import Image


@pyrogram.Client.on_message(pyrogram.filters.command(["c2v"]))
async def convert_to_video(bot, update):
    update_channel = Config.UPDATE_CHANNEL
    if update_channel:
        try:
            user = await bot.get_chat_member(update_channel, update.chat.id)
            if user.status == "kicked":
               await update.reply_text(" Sorry, You are **B A N N E D**")
               return
        except UserNotParticipant:

            await update.reply_text(
                text="**Please Join My Update Channel Before Using Me..**",
                reply_markup=InlineKeyboardMarkup([
                    [ InlineKeyboardButton(text="Join My Updates Channel", url=f"https://t.me/{update_channel}")]
              ])
            )
            return  

    if update.reply_to_message is not None:
        
        download_location = Config.DOWNLOAD_LOCATION + "/"
        file_name=download_location
        a = await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.DOWNLOAD_START,
            reply_to_message_id=update.message_id
        )
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=update.reply_to_message,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                Translation.DOWNLOAD_START,
                a,
                c_time
            )
        )
        if the_real_download_location is not None:
            await bot.edit_message_text(
                text=Translation.SAVED_RECVD_DOC_FILE,
                chat_id=update.chat.id,
                message_id=a.message_id
            )

            logger.info(the_real_download_location)

            width = 0
            height = 0
            duration = 0
            metadata = extractMetadata(createParser(the_real_download_location))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            thumb_image_path = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
            if not os.path.exists(thumb_image_path):
                thumb_image_path = await take_screen_shot(
                    the_real_download_location,
                    os.path.dirname(the_real_download_location),
                    random.randint(
                        0,
                        duration - 1
                    )
                )
            logger.info(thumb_image_path)

            metadata = extractMetadata(createParser(thumb_image_path))
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")

            Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
            img = Image.open(thumb_image_path)

            img.resize((90, height))
            img.save(thumb_image_path, "JPEG")

            c_time = time.time()
            await bot.send_video(
                chat_id=update.chat.id,
                video=the_real_download_location,
                caption=f"<b>{file_name}</b>",
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,

                thumb=thumb_image_path,
                reply_to_message_id=update.reply_to_message.message_id,
                progress=progress_for_pyrogram,
                progress_args=(
                    Translation.UPLOAD_START,
                    a,
                    c_time
                )
            )
            try:
                os.remove(the_real_download_location)

            except:
                pass
            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.chat.id,
                message_id=a.message_id,
                disable_web_page_preview=True
            )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_FILE_FOR_CONVERT,
            reply_to_message_id=update.message_id
        )
