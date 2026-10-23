from utils import get_random_mix_id, get_size, is_subscribed, is_req_subscribed, group_setting_buttons, get_poster, get_posterx, temp, get_settings, save_group_settings, get_cap, imdb, is_check_admin, extract_request_content, log_error, clean_filename, generate_season_variations, clean_search_text, get_settings_text
from rapidfuzz import process
from dreamxbotz.util.file_properties import get_name, get_hash
from urllib.parse import quote_plus
import logging
from database.ia_filterdb import Media, Media2, get_search_results, get_bad_files
from database.config_db import mdb
from pyrogram.errors import MessageIdInvalid, UserIsBlocked, MessageNotModified, PeerIdInvalid
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, LinkPreviewOptions
from info import (
    ADMINS, AUTH_CHANNELS, AUTH_REQ_CHANNELS, BIN_CHANNEL, DELETE_TIME,
    EMOJI_MODE, GRP_LNK, LANDSCAPE_POSTER, LANGUAGES, LOG_CHANNEL, MAX_B_TN, MSG_ALRT,
    MULTIPLE_DB, NO_RESULTS_MSG, OWNER_LNK, OWNER_UPI_ID, PICS, PICS_URL, QR_CODE, QUALITIES,
    REACTIONS, REQST_CHANNEL, SEASONS, STAR_PREMIUM_PLANS, SUBSCRIPTION, SUPPORT_CHAT_ID,
    TMDB_ON_SEARCH, TMDB_POSTER, ULTRA_FAST_MODE, UPDATE_CHNL_LNK, URL, FQDN, PORT
)
from Script import script
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from database.refer import referdb
from database.users_chats_db import db
import asyncio
import re
import math
import random
import pytz
from datetime import datetime, timedelta
lock = asyncio.Lock()

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
BUTTONS0 = {}
BUTTONS1 = {}
BUTTONS2 = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming & ~filters.regex(r"^/"))
async def give_filter(client, message):
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception:
            try:
                await message.react(emoji="⚡️")
            except Exception:
                pass
    await mdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        try:
            if settings['auto_ffilter']:
                if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                    if await is_check_admin(client, message.chat.id, message.from_user.id):
                        return
                    return await message.delete()
                await auto_filter(client, message)
        except KeyError:
            await save_group_settings(message.chat.id, 'auto_ffilter', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_ffilter']:
                await auto_filter(client, message)
        except Exception as e:
            logger.exception("Error in auto filter: %s", e)
            pass
    else:
        search = message.text
        _, _, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        await message.reply_text(
            script.ALREADY_AVAILABLE_TXT.format(message.from_user.mention, total_results, search),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]])
        )


@Client.on_message(filters.private & filters.text & filters.incoming & ~filters.regex(r"^/") & ~filters.regex(r"(https?://)?(t\.me|telegram\.me|telegram\.dog)/"), group=1)
async def pm_text(bot, message):
    bot_id = temp.ME
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id

    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception:
            try:
                await message.react(emoji="⚡️")
            except Exception:
                pass

    if content.startswith("#"):
        return

    try:
        await mdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)

        if pm_search:
            await auto_filter(bot, message)
        else:
            logger.info(f"🚫 PM Search Disabled For User: {user_id}")
            try:
                await message.reply_text(
                    text=script.PM_SEARCH_DISABLED_TXT.format(user=user),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⚝ ᴍɪss ᴘʀᴏᴠɪᴅᴇʀ ʀᴇǫᴜᴇsᴛ ⚝", url=GRP_LNK)]
                    ])
                )
            except Exception as e:
                logger.error(f"❌ Failed to send PM_SEARCH_DISABLED message: {e}")
                try:
                    await message.reply_text(
                        f"<b>🙋 Hey {user},\n\nʏᴏᴜ ᴄᴀɴ sᴇᴀʀᴄʜ ᴏɴʟʏ ɪɴ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ!\n\n📝 ᴘʟᴇᴀsᴇ ʀᴇǫᴜᴇsᴛ ɪɴ: {GRP_LNK}</b>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⚝ ᴍɪss ᴘʀᴏᴠɪᴅᴇʀ ʀᴇǫᴜᴇsᴛ ⚝", url=GRP_LNK)]
                        ])
                    )
                except Exception as e2:
                    logger.error(f"❌ Fallback message also failed: {e2}")

            try:
                await bot.send_message(
                    chat_id=LOG_CHANNEL,
                    text=script.PM_LOG_TXT.format(user, user_id, content)
                )
            except Exception as e:
                logger.error(f"❌ Failed to log PM message: {e}")

    except Exception as e:
        logger.error(f"❌ Error in pm_text handler: {e}", exc_info=True)


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('invite link', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('Back', callback_data='premium_info')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    try:
        await bot.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto("https://graph.org/file/1a2e64aee3d4d10edd930.jpg")
        )
    except Exception:
        pass
    await query.message.edit_text(
        text=script.REFER_TXT.format(bot.me.username, query.from_user.id),
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        await query.answer()
    except Exception:
        pass
    ident, req, key, offset = query.data.split("_")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    if BUTTONS.get(key) is not None:
        search = BUTTONS.get(key)
    else:
        search = FRESH.get(key)

    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        if match:
            search = match.group(1).strip()
            FRESH[key] = search
        else:
            for line in raw_text.splitlines():
                if "🏷" in line and ":" in line:
                    search = line.split(":", 1)[1].strip()
                    search = re.sub(r"<.*?>", "", search).strip()
                    if search:
                        FRESH[key] = search
                        break

    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except Exception:
        n_offset = 0

    if not files:
        return
    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)

    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0, [
            InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])
        btn.insert(0, [
            InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
        ])
    else:
        btn = [
            [
                InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
            ],
            [
                InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
            ]
        ]

    if ULTRA_FAST_MODE:
        if 0 < offset <= 10:
            off_set = 0
        elif offset == 0:
            off_set = None
        else:
            off_set = offset - 10

        if n_offset == 0:
            btn.append([
                InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages")
            ])
        elif off_set is None:
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"),
                InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
            ])
        else:
            btn.append([
                InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.SUCCESS)
            ])
    else:
        try:
            if settings['max_btn']:
                if 0 < offset <= 10:
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - 10

                if n_offset == 0:
                    btn.append([
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.DANGER)
                    ])
                elif off_set is None:
                    btn.append([
                        InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                    ])
                else:
                    btn.append([
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                    ])
            else:
                max_b = int(MAX_B_TN)
                if 0 < offset <= max_b:
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - max_b

                if n_offset == 0:
                    btn.append([
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/max_b)+1} / {math.ceil(total/max_b)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS)
                    ])
                elif off_set is None:
                    btn.append([
                        InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/max_b)+1} / {math.ceil(total/max_b)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                    ])
                else:
                    btn.append([
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/max_b)+1} / {math.ceil(total/max_b)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                    ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10

            if n_offset == 0:
                btn.append([
                    InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY)
                ])
            elif off_set is None:
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                ])
            else:
                btn.append([
                    InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                ])

    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        dreamx_title = clean_search_text(search)
        try:
            if settings['imdb']:
                cap = await get_cap(settings, remaining_seconds, files, query, total, dreamx_title, offset)
                if query.message.caption:
                    try:
                        await query.message.edit_caption(caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    except (MessageNotModified, MessageIdInvalid):
                        pass
                else:
                    try:
                        await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    except (MessageNotModified, MessageIdInvalid):
                        pass
            else:
                cap = await get_cap(settings, remaining_seconds, files, query, total, dreamx_title, offset+1)
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
        except (MessageNotModified, MessageIdInvalid):
            pass
        except Exception as e:
            logger.exception("Failed to send result: %s", e)
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except (MessageNotModified, MessageIdInvalid):
            pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    movie_title = None
    try:
        if query.message and query.message.reply_markup:
            for row in query.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data == query.data:
                        movie_title = btn.text
                        break
                if movie_title:
                    break
    except Exception:
        pass
    if not movie_title:
        try:
            parts = query.data.split('#')
            if len(parts) >= 3:
                movie_title = "#".join(parts[1:-1])
        except Exception:
            pass
    if not movie_title:
        movie_title = "Movie"
    try:
        parts = query.data.split('#')
        user_id = parts[-1] if len(parts) >= 2 else "0"
        if int(user_id) != 0 and query.from_user.id != int(user_id):
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    except Exception:
        pass
    movie_title = re.sub(r"[:-]", " ", movie_title)
    movie_title = re.sub(r"\s+", " ", movie_title).strip()
    await query.answer(f"Searching for {movie_title}...", show_alert=False)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie_title, offset=0, filter=True)
    if not files:
        files, offset, total_results = await get_search_results(query.message.chat.id, movie_title.lower(), offset=0, filter=True)
    if files:
        k = (movie_title, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        try:
            reqstr = await bot.get_users(reqstr1)
        except Exception:
            reqstr = query.from_user
        if NO_RESULTS_MSG:
            try:
                await bot.send_message(chat_id=BIN_CHANNEL, text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie_title))
            except Exception as e:
                logger.error("Error In Spol: %s", e)
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("ʀᴇǫᴜᴇsᴛ 📝 ᴀᴅᴍɪɴ", url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)]])
        try:
            k = await query.message.edit_text(text=script.MVE_NT_FND.format(movie_title), reply_markup=btn)
            await asyncio.sleep(10)
            await k.delete()
        except Exception:
            pass


@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace(' ', '_')
    btn = []
    for i in range(0, len(QUALITIES), 2):
        q1 = QUALITIES[i]
        row = [InlineKeyboardButton(text=q1, callback_data=f"fq#{q1.lower()}#{req}#{key}")]
        if i + 1 < len(QUALITIES):
            q2 = QUALITIES[i + 1]
            row.append(InlineKeyboardButton(text=q2, callback_data=f"fq#{q2.lower()}#{req}#{key}"))
        btn.append(row)

    btn.insert(0, [
        InlineKeyboardButton(text="⇊ ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ⇊", callback_data="ident", style=enums.ButtonStyle.PRIMARY)
    ])
    btn.append([
        InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"fq#homepage#{req}#{key}", style=enums.ButtonStyle.SUCCESS)
    ])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    _, qual, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace("_", " ")
    if qual in search:
        search = search.replace(qual, "")
    chat_id = query.message.chat.id
    message = query.message
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    except Exception:
        pass
    if qual != "homepage":
        search = f"{search} {qual}"
    BUTTONS[key] = search
    files, offset, total_results = await get_search_results(chat_id, search, offset=0, filter=True)
    if not files:
        await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
        return
    temp.GETALL[key] = files
    settings = await get_settings(message.chat.id)

    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0, [
            InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])
        btn.insert(0, [
            InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
        ])
    else:
        btn = [
            [
                InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
            ],
            [
                InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
            ]
        ]

    if offset != "":
        try:
            if settings['max_btn']:
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
            else:
                max_b = int(MAX_B_TN)
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/max_b)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
            ])
    else:
        btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.DANGER)])

    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        dreamx_title = clean_search_text(search)
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, dreamx_title, offset=1)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
        except (MessageNotModified, MessageIdInvalid):
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except (MessageNotModified, MessageIdInvalid):
            pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace(' ', '_')
    items = list(LANGUAGES.items())
    btn = []
    for i in range(0, len(items), 2):
        name1, code1 = items[i]
        row = [InlineKeyboardButton(text=name1, callback_data=f"fl#{code1}#{req}#{key}")]
        if i + 1 < len(items):
            name2, code2 = items[i + 1]
            row.append(InlineKeyboardButton(text=name2, callback_data=f"fl#{code2}#{req}#{key}"))
        btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="⇊ ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ ⇊", callback_data="ident", style=enums.ButtonStyle.SUCCESS)])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"fl#homepage#{req}#{key}", style=enums.ButtonStyle.PRIMARY)])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace("_", " ")
    if lang in search:
        search = search.replace(lang, "")
    chat_id = query.message.chat.id
    message = query.message
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    except Exception:
        pass
    if lang != "homepage":
        search = f"{search} {lang}"
    BUTTONS[key] = search
    files, offset, total_results = await get_search_results(chat_id, search, offset=0, filter=True)
    if not files:
        await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
        return
    temp.GETALL[key] = files
    settings = await get_settings(message.chat.id)

    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0, [
            InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])
        btn.insert(0, [
            InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
        ])
    else:
        btn = [
            [
                InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
            ],
            [
                InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
            ]
        ]

    if offset != "":
        try:
            if settings['max_btn']:
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
            else:
                max_b = int(MAX_B_TN)
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/max_b)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
            ])
    else:
        btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.PRIMARY)])

    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        dreamx_title = clean_search_text(search)
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, dreamx_title, offset=1)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
        except (MessageNotModified, MessageIdInvalid):
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except (MessageNotModified, MessageIdInvalid):
            pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ…",
                show_alert=True,
            )
    except Exception:
        pass
    offset = 0
    btn = []
    for i in range(0, len(SEASONS) - 1, 2):
        btn.append([
            InlineKeyboardButton(f"𝐒ᴇᴀꜱᴏɴ {SEASONS[i][1:]}", callback_data=f"fs#{SEASONS[i].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton(f"𝐒ᴇᴀꜱᴏɴ {SEASONS[i+1][1:]}", callback_data=f"fs#{SEASONS[i+1].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])

    btn.insert(0, [InlineKeyboardButton("⇊ ꜱᴇʟᴇᴄᴛ ꜱᴇᴀꜱᴏɴ ⇊", callback_data="ident", style=enums.ButtonStyle.SUCCESS)])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ​↭", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.PRIMARY)])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_seasons_cb_handler(client: Client, query: CallbackQuery):
    start_t = datetime.now(pytz.timezone("Asia/Kolkata"))
    _, season_tag, req, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE|Title)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace("_", " ")
    season_tag = season_tag.lower()
    if season_tag == "homepage":
        search_final = search
        query_input = search_final
    else:
        season_number = int(season_tag[1:])
        query_input = generate_season_variations(search, season_number)
        search_final = query_input[0] if query_input else search

    BUTTONS[key] = search_final
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer("⚠️ Not your request", show_alert=True)
    except Exception:
        pass

    chat_id = query.message.chat.id
    files, n_offset, total_results = await get_search_results(chat_id, query_input, offset=0, filter=True)
    if not files:
        BUTTONS[key] = None
        return await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ 🚫", show_alert=True)

    temp.GETALL[key] = files
    settings = await get_settings(chat_id)
    btn = []
    if settings.get("button"):
        btn.extend([
            [InlineKeyboardButton(f"{get_size(f.file_size)} ≽ " + clean_filename(f.file_name), callback_data=f"file#{f.file_id}")]
            for f in files
        ])
    btn.insert(0, [
        InlineKeyboardButton("𝐐ᴜᴀʟɪᴛʏ", callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
        InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("𝐒ᴇᴀꜱᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER),
    ])
    btn.insert(0, [
        InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
    ])

    if n_offset != "":
        try:
            if settings['max_btn']:
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                ])
            else:
                max_b = int(MAX_B_TN)
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/max_b)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
            ])
    else:
        btn.append([InlineKeyboardButton(text="↭  ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.PRIMARY)])

    if not settings.get("button"):
        time_difference = datetime.now(pytz.timezone("Asia/Kolkata")) - start_t
        remaining_seconds = f"{time_difference.total_seconds():.2f}"
        dreamx_title = clean_search_text(search_final)
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, dreamx_title, offset=1)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))
        except (MessageNotModified, MessageIdInvalid):
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except (MessageNotModified, MessageIdInvalid):
            pass
    await query.answer()


@Client.on_callback_query(group=10)
async def cb_handler(client: Client, query: CallbackQuery):
    DreamxData = query.data
    try:
        await client.create_chat_invite_link(int(REQST_CHANNEL))
    except Exception:
        pass
    if query.data == "close_data":
        try:
            user = query.message.reply_to_message.from_user.id
        except Exception:
            user = query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.NT_ALRT_TXT, show_alert=True)
        await query.answer("ᴛʜᴀɴᴋs ꜰᴏʀ ᴄʟᴏsᴇ 🙈")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass

    elif query.data == "pages":
        await query.answer("ᴛʜɪs ɪs ᴘᴀɢᴇs ʙᴜᴛᴛᴏɴ 😅")

    elif query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = query.message.reply_to_message.from_user.id if query.message.reply_to_message else query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")

    elif query.data.startswith("sendfiles"):
        ident, key = query.data.split("#")
        try:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{query.message.chat.id}_{key}")
            return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")

    elif query.data.startswith("autofilter_delete"):
        await Media.collection.drop()
        if MULTIPLE_DB:
            await Media2.collection.drop()
        await query.answer("Eᴠᴇʀʏᴛʜɪɴɢ's Gᴏɴᴇ")
        await query.message.edit('ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ ✅')

    elif query.data.startswith("checksub"):
        try:
            ident, kk, file_id = query.data.split("#")
            btn = []
            chat = file_id.split("_")[0]
            try:
                chat_id = int(chat)
            except Exception:
                chat_id = 0

            settings = await get_settings(chat_id) if chat_id else None
            custom_fsub = (settings.get('fsub') or settings.get('fsub_id')) if settings else None

            if custom_fsub:
                if not isinstance(custom_fsub, list):
                    custom_fsub = [custom_fsub]
                custom_fsub_ids = [int(x) for x in custom_fsub if x]
                if custom_fsub_ids:
                    btn += await is_subscribed(client, query.from_user.id, custom_fsub_ids)
            else:
                if AUTH_CHANNELS:
                    btn += await is_subscribed(client, query.from_user.id, AUTH_CHANNELS)
                if AUTH_REQ_CHANNELS:
                    btn += await is_req_subscribed(client, query.from_user.id, AUTH_REQ_CHANNELS)
            if btn:
                btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{kk}#{file_id}", style=enums.ButtonStyle.PRIMARY)])
                try:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
                except (MessageNotModified, MessageIdInvalid):
                    pass
                await query.answer(
                    f"👋 Hello {query.from_user.first_name},\n\n"
                    "🛑 Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴜᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟs.\n"
                    "👉 Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴇᴀᴄʜ ᴏɴᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.\n",
                    show_alert=True
                )
                return
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
            if query.message.chat.type == enums.ChatType.PRIVATE:
                await query.message.delete()
        except Exception as e:
            await log_error(client, f"❌ Error in checksub callback:\n\n{repr(e)}")
            logger.error(f"❌ Error in checksub callback:\n\n{repr(e)}")

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>ꜰɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇꜱꜱ ᴡɪʟʟ ꜱᴛᴀʀᴛ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({'_id': file_ids})
                    if not result.deleted_count and MULTIPLE_DB:
                        result = await Media2.collection.delete_one({'_id': file_ids})
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ... ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ</b>")
            except Exception as e:
                logger.error("Error In killfiledq: %s", e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ</b>")

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
        ):
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            btn = await group_setting_buttons(int(grp_id))
            await query.message.edit_text(text=await get_settings_text(grp_id, title), parse_mode=enums.ParseMode.HTML)
            await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))

    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[InlineKeyboardButton("ᴄʜᴇᴄᴋ ᴍʏ ᴅᴍ 🗳️", url=f"telegram.me/{temp.U_NAME}", style=enums.ButtonStyle.SUCCESS)]]
        await query.message.edit_text(f"<b>ʏᴏᴜʀ sᴇᴛᴛɪɴgs ᴍᴇɴᴜ ғᴏʀ {title} ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>")
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn2))
        if settings is not None:
            btn = await group_setting_buttons(int(grp_id))
            await client.send_message(
                chat_id=userid,
                text=await get_settings_text(grp_id, title),
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
            InlineKeyboardButton("⚠️ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", callback_data=f"unavailable#{from_user}"),
            InlineKeyboardButton("🟢 ᴜᴘʟᴏᴀᴅᴇᴅ 🟢", callback_data=f"uploaded#{from_user}")
        ], [
            InlineKeyboardButton("♻️ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ♻️", callback_data=f"already_available#{from_user}")
        ], [
            InlineKeyboardButton("📌 Not Released 📌", callback_data=f"Not_Released#{from_user}"),
            InlineKeyboardButton("♨️Type Correct Spelling♨️", callback_data=f"Type_Correct_Spelling#{from_user}")
        ], [
            InlineKeyboardButton("⚜️ Not Available In The Hindi ⚜️", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
        ]]
        if query.from_user.id in ADMINS:
            await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.split("#")[0] in ["unavailable", "Not_Released", "Type_Correct_Spelling", "Not_Available_In_The_Hindi", "uploaded", "already_available"]:
        key = query.data.split("#")[0]
        ident, from_user = query.data.split("#")
        if query.from_user.id not in ADMINS:
            return await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

        status_configs = {
            "unavailable": {
                "btn_text": "⚠️ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", "alert_key": "unalert", "answer": "Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !",
                "pm": "<b>Hᴇʏ {mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
                "sup": "<b>Hᴇʏ {mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>",
                "search": False
            },
            "Not_Released": {
                "btn_text": "📌 Not Released 📌", "alert_key": "nralert", "answer": "Sᴇᴛ ᴛᴏ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ !",
                "pm": "<b>Hᴇʏ {mention}\n\n<code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️</b>",
                "sup": "<u>Hᴇʏ {mention}</u>\n\n<b><code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
                "search": False
            },
            "Type_Correct_Spelling": {
                "btn_text": "♨️ Type Correct Spelling ♨️", "alert_key": "wsalert", "answer": "Sᴇᴛ ᴛᴏ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ !",
                "pm": "<b>Hᴇʏ {mention}\n\nWᴇ Dᴇᴄʟɪɴᴇᴅ Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑</b>",
                "sup": "<u>Hᴇʏ {mention}</u>\n\n<b><code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
                "search": False
            },
            "Not_Available_In_The_Hindi": {
                "btn_text": "⚜️ Not Available In The Hindi ⚜️", "alert_key": "hnalert", "answer": "Sᴇᴛ ᴛᴏ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ Iɴ Hɪɴᴅɪ !",
                "pm": "<b>Hᴇʏ {mention}\n\nYᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌</b>",
                "sup": "<u>Hᴇʏ {mention}</u>\n\n<b><code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
                "search": False
            },
            "uploaded": {
                "btn_text": "🟢 ᴜᴘʟᴏᴀᴅᴇᴅ 🟢", "alert_key": "upalert", "answer": "Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !",
                "pm": "<b>Hᴇʏ {mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n#Uᴘʟᴏᴀᴅᴇᴅ✅",
                "sup": "<u>{content}</u>\n\n<b>Hᴇʏ {mention}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n#Uᴘʟᴏᴀᴅᴇᴅ✅\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>",
                "search": True
            },
            "already_available": {
                "btn_text": "♻️ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ♻️", "alert_key": "alalert", "answer": "Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !",
                "pm": "<b>Hᴇʏ {mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n#Aᴠᴀɪʟᴀʙʟᴇ 💗",
                "sup": "<b>Hᴇʏ {mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n#Aᴠᴀɪʟᴀʙʟᴇ 💗\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢES.</small>",
                "search": True
            }
        }
        cfg = status_configs[key]
        user = await client.get_users(from_user)
        btn = [[InlineKeyboardButton(cfg["btn_text"], callback_data=f'{cfg["alert_key"]}#{from_user}')]]
        btn2 = [[
            InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=UPDATE_CHNL_LNK, style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}", style=enums.ButtonStyle.PRIMARY)
        ]]
        if cfg["search"]:
            btn2.append([InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK, style=enums.ButtonStyle.SUCCESS)])

        content = query.message.text
        await query.message.edit_text(f"<b><strike>{content}</strike></b>")
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
        await query.answer(cfg["answer"])

        req_content = extract_request_content(query.message.text)
        try:
            await client.send_message(
                chat_id=int(from_user),
                text=cfg["pm"].format(mention=user.mention, content=req_content),
                reply_markup=InlineKeyboardMarkup(btn2)
            )
        except UserIsBlocked:
            await client.send_message(
                chat_id=int(SUPPORT_CHAT_ID),
                text=cfg["sup"].format(mention=user.mention, content=req_content),
                reply_markup=InlineKeyboardMarkup(btn2)
            )

    elif query.data.split("#")[0] in ["alalert", "upalert", "unalert", "hnalert", "nralert", "wsalert"]:
        ident, from_user = query.data.split("#")
        alerts = {
            "alalert": "Hᴇʏ {name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ ✅",
            "upalert": "Hᴇʏ {name}, Yᴏᴜʀ ʀᴇǫᴜESꜱᴛ ɪꜱ Uᴘʟᴏᴀᴅᴇᴅ 🔼",
            "unalert": "Hᴇʏ {name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
            "hnalert": "Hᴇʏ {name}, Tʜɪꜱ ɪꜱ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ❌",
            "nralert": "Hᴇʏ {name}, Tʜᴇ Mᴏᴠɪᴇ/ꜱʜᴏᴡ ɪꜱ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ Yᴇᴛ 🆕",
            "wsalert": "Hᴇʏ {name}, Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ ᴅᴜᴇ ᴛᴏ ᴡʀᴏɴɢ sᴘᴇʟʟɪɴɢ ❗"
        }
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            msg_text = alerts[ident].format(name=user.first_name)
            await query.answer(msg_text, show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇᴇ ᴛʜɪꜱ ❌", show_alert=True)

    elif DreamxData.startswith("generate_stream_link"):
        _, file_id = DreamxData.split(":")
        try:
            target_channel = BIN_CHANNEL
            if not target_channel or target_channel == -100:
                if LOG_CHANNEL and LOG_CHANNEL != -100:
                    target_channel = LOG_CHANNEL
                else:
                    try:
                        await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file_id,
                            caption="✅ <b>Here is your file directly!</b>"
                        )
                        await query.answer("✅ Sent file directly to your PM!", show_alert=True)
                        return
                    except Exception:
                        await query.answer("⚠️ BIN_CHANNEL / LOG_CHANNEL is not configured!", show_alert=True)
                        return

            user_id = query.from_user.id
            username = query.from_user.mention if query.from_user else f"User {user_id}"
            log_msg = None

            try:
                log_msg = await client.send_cached_media(chat_id=target_channel, file_id=file_id)
            except Exception as channel_err:
                logger.warning("Failed sending to channel %s: %s", target_channel, channel_err)
                if target_channel != LOG_CHANNEL and LOG_CHANNEL and LOG_CHANNEL != -100:
                    try:
                        log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
                        target_channel = LOG_CHANNEL
                    except Exception as log_err:
                        logger.error("Fallback to LOG_CHANNEL failed: %s", log_err)

            if not log_msg:
                try:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption="✅ <b>Here is your file directly!</b>"
                    )
                    await query.answer("✅ Sent file directly to your PM!", show_alert=True)
                    return
                except Exception as dm_err:
                    await query.answer("⚠️ Bot is not Admin in channel!", show_alert=True)
                    return

            raw_file_name = get_name(log_msg) or getattr(log_msg, 'caption', None) or 'file'
            file_name_clean = str(raw_file_name).strip() if raw_file_name else 'file'
            fileName = quote_plus(file_name_clean)
            file_hash = get_hash(log_msg) if hasattr(log_msg, 'id') else ''

            def _is_valid_url(u: str) -> bool:
                if not u or not isinstance(u, str):
                    return False
                val = u.strip()
                if not (val.startswith("https://") or val.startswith("http://") or val.startswith("tg://")):
                    return False
                low = val.lower()
                for bad in ["localhost", "0.0.0.0", "127.0.0.1", "http://:/", "https://:/"]:
                    if bad in low:
                        return False
                host = re.sub(r'^https?://', '', val).split('/')[0].split(':')[0]
                return bool(host and '.' in host)

            stream_base_url = URL.strip() if (URL and _is_valid_url(URL)) else ""
            if not stream_base_url and FQDN and _is_valid_url(f"https://{FQDN}/"):
                stream_base_url = f"https://{FQDN}/"

            has_valid_url = bool(stream_base_url and _is_valid_url(stream_base_url))

            if has_valid_url:
                if not stream_base_url.endswith("/"):
                    stream_base_url += "/"
                dreamx_stream = f"{stream_base_url}watch/{str(log_msg.id)}/{fileName}?hash={file_hash}"
                dreamx_download = f"{stream_base_url}{str(log_msg.id)}/{fileName}?hash={file_hash}"
            else:
                dreamx_stream = ""
                dreamx_download = ""

            clean_update = str(UPDATE_CHNL_LNK).strip() if UPDATE_CHNL_LNK else ""
            if clean_update.startswith("@"):
                clean_update = f"https://t.me/{clean_update[1:]}"
            elif clean_update and not clean_update.startswith("http"):
                clean_update = f"https://t.me/{clean_update}"
            if not clean_update or not _is_valid_url(clean_update):
                clean_update = "https://t.me/telegram"

            log_btn = []
            if has_valid_url:
                log_btn = [[
                    InlineKeyboardButton("🚀 ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ", url=dreamx_download),
                    InlineKeyboardButton('🖥️ ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ', url=dreamx_stream)
                ]]

            log_text = f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id}\n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username}\n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {file_name_clean}"

            try:
                await client.send_message(
                    chat_id=target_channel,
                    text=log_text,
                    reply_to_message_id=log_msg.id,
                    reply_markup=InlineKeyboardMarkup(log_btn) if log_btn else None
                )
            except Exception:
                pass

            if has_valid_url:
                try:
                    await query.answer(MSG_ALRT)
                except Exception:
                    pass

                try:
                    dreamcinezone = await query.edit_message_reply_markup(
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("🚀 ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ ", url=dreamx_download, style=enums.ButtonStyle.PRIMARY),
                                InlineKeyboardButton('🖥️ ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ 🖥️', url=dreamx_stream, style=enums.ButtonStyle.SUCCESS)
                            ],
                            [
                                InlineKeyboardButton('🌹 𝐉ᴏɪɴ 𝐔ᴩᴅᴀᴛᴇꜱ 𝐂ʜᴀɴɴᴇʟ 🌹', url=clean_update, style=enums.ButtonStyle.DANGER)
                            ]
                        ])
                    )
                    if DELETE_TIME:
                        await asyncio.sleep(DELETE_TIME)
                        try:
                            await dreamcinezone.delete()
                        except Exception:
                            pass
                    return
                except Exception as edit_err:
                    logger.error("Failed to edit reply markup: %s", edit_err)

            try:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f"✅ <b>{file_name_clean}</b>\n\n⚠️ <i>Web Stream requires domain setup in .env</i>"
                )
            except Exception:
                pass

            await query.answer("File sent directly to your PM!", show_alert=True)
            return

        except Exception as e:
            logger.error("Callback error in generate_stream_link: %s", e)
            try:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption="✅ <b>Here is your file directly!</b>"
                )
                await query.answer("✅ Sent file directly to your PM!", show_alert=True)
            except Exception:
                await query.answer("⚠️ Stream link error occurred", show_alert=True)
            return

    elif query.data == "prestream":
        await query.answer(text=script.PRE_STREAM_ALERT, show_alert=True)
        dreamcinezone = await client.send_photo(
            chat_id=query.message.chat.id,
            photo="https://i.ibb.co/whf8xF7j/photo-2025-07-26-10-42-46-7531339305176793100.jpg",
            caption=script.PRE_STREAM,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 𝐁𝐔𝐘 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 🚀", callback_data="premium_info", style=enums.ButtonStyle.DANGER)]
            ])
        )
        await asyncio.sleep(DELETE_TIME)
        try:
            await dreamcinezone.delete()
        except Exception:
            pass

    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('✧ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ✧', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true', style=enums.ButtonStyle.SUCCESS)
        ], [
            InlineKeyboardButton('𖣠‌ ʜᴇʟᴘ 𖣠‌ ', callback_data="help", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton('᪥ ᴀʙᴏᴜᴛ ᪥', callback_data="about", style=enums.ButtonStyle.PRIMARY),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞"
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 🌓"
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 🌑"
        try:
            try:
                PIC = f"{random.choice(PICS_URL)}?r={get_random_mix_id()}"
            except Exception:
                PIC = random.choice(PICS)
            await client.edit_message_media(
                query.message.chat.id,
                query.message.id,
                InputMediaPhoto(PIC)
            )
        except Exception:
            pass
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer(MSG_ALRT)

    elif query.data == "donation":
        buttons = [[
            InlineKeyboardButton('🌲 Sᴇɴᴅ Dᴏɴᴀᴛᴇ Sᴄʀᴇᴇɴsʜᴏᴛ Hᴇʀᴇ', url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)
        ], [
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='about', style=enums.ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto('https://graph.org/file/99eebf5dbe8a134f548e0.jpg')
        )
        await query.message.edit_text(
            text=script.DREAMXBOTZ_DONATION.format(query.from_user.mention, QR_CODE, OWNER_UPI_ID),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start', style=enums.ButtonStyle.DANGER)
        ]]
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('❃ ɢʀᴏᴜᴘ ❃', url='https://t.me/movies_4uz', style=enums.ButtonStyle.SUCCESS),
            InlineKeyboardButton(' ⫹⫺ ᴄʜᴀɴɴᴇʟ ⫹⫺ ', url='https://t.me/movies4u_backup', style=enums.ButtonStyle.SUCCESS),
        ], [
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start', style=enums.ButtonStyle.DANGER)
        ]]
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer(
                    "🚸 ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴏɴᴄᴇ !\n\n📌 ᴄʜᴇᴄᴋᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ ʙʏ : /plan",
                    show_alert=True
                )
                return
            else:
                await db.give_free_trial(user_id)
                await query.answer("✅ Trial activated!", show_alert=True)
                msg = await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo="https://i.ibb.co/0jC8MSDZ/photo-2025-07-26-10-42-36-7531339283701956616.jpg",
                    caption="<b>🥳 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ\n\n🎉 ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ <u>5 ᴍɪɴᴜᴛᴇs</u> ꜰʀᴏᴍ ɴᴏᴡ !\n\nɴᴇᴇᴅ ᴘʀᴇᴍɪᴜᴍ 👉🏻 /plan</b>",
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🚀 𝐁𝐔𝐘 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 🚀", callback_data="premium_info", style=enums.ButtonStyle.PRIMARY)
                    ]])
                )
                await asyncio.sleep(DELETE_TIME)
                return await msg.delete()
        except Exception:
            logging.exception("Error in give_trial callback")

    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('ᴩʀᴏᴠɪᴅᴇʀʙᴏᴛᴢ', url='https://tx.me/ProviderBotz', style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='about', style=enums.ButtonStyle.DANGER)
        ]]
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)

    elif query.data == "disclaimer":
        btn = [[InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="about", style=enums.ButtonStyle.PRIMARY)]]
        await query.message.edit_text(
            text=script.DISCLAIMER_TXT,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "premium_info":
        try:
            btn = [[
                InlineKeyboardButton('• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •', callback_data='buy_info', style=enums.ButtonStyle.PRIMARY),
            ], [
                InlineKeyboardButton('• ʀᴇꜰᴇʀ ꜰʀɪᴇɴᴅꜱ', callback_data='reffff', style=enums.ButtonStyle.SUCCESS),
                InlineKeyboardButton('ꜰʀᴇᴇ ᴛʀɪᴀʟ •', callback_data='give_trial', style=enums.ButtonStyle.PRIMARY)
            ], [
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start', style=enums.ButtonStyle.DANGER)
            ]]
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.BPREMIUM_TXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass

    elif query.data == "buy_info":
        try:
            btn = [[
                InlineKeyboardButton('ꜱᴛᴀʀ', callback_data='star_info', style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton('ᴜᴘɪ', callback_data='upi_info', style=enums.ButtonStyle.PRIMARY)
            ], [
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ⇋', callback_data='premium_info', style=enums.ButtonStyle.DANGER)
            ]]
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_TEXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass

    elif query.data == "upi_info":
        try:
            btn = [[
                InlineKeyboardButton('• ꜱᴇɴᴅ  ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ •', url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY),
            ], [
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='buy_info', style=enums.ButtonStyle.DANGER)
            ]]
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_UPI_TEXT.format(OWNER_UPI_ID), parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass

    elif query.data == "star_info":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}⭐", callback_data=f"buy_{stars}", style=enums.ButtonStyle.PRIMARY)
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="buy_info", style=enums.ButtonStyle.DANGER)])
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_STAR_TEXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            pass

    elif query.data.startswith("grp_pm"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer(script.NT_ADMIN_ALRT_TXT, show_alert=True)
        btn = await group_setting_buttons(int(grp_id))
        dreamx = await client.get_chat(int(grp_id))
        await query.message.edit(text=await get_settings_text(grp_id, dreamx.title), reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

    elif query.data.startswith("removegrp"):
        user_id = query.from_user.id
        grp_id = int(query.data.split("#")[1])
        if not await is_check_admin(client, grp_id, query.from_user.id):
            return await query.answer(script.NT_ADMIN_ALRT_TXT, show_alert=True)
        await db.remove_group_connection(grp_id, user_id)
        await query.answer("Group removed from your connections.", show_alert=True)
        connected_groups = await db.get_connected_grps(user_id)
        if not connected_groups:
            await query.edit_message_text("Nᴏ Cᴏɴɴᴇᴄᴛᴇᴅ Gʀᴏᴜᴘs Fᴏᴜɴᴅ .")
            return
        group_list = []
        for group in connected_groups:
            try:
                Chat = await client.get_chat(group)
                group_list.append([InlineKeyboardButton(text=Chat.title, callback_data=f"grp_pm#{Chat.id}")])
            except Exception:
                pass
        await query.edit_message_text(
            "⚠️ ꜱᴇʟᴇᴄᴛ ᴛʜᴇ ɢʀᴏᴜᴘ ᴡʜᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ.\n\nɪꜰ ʏᴏᴜʀ ɢʀᴏᴜᴘ ɪꜱ ɴᴏᴛ ꜱʜᴏᴡɪɴɢ ʜᴇʀᴇ,\nᴜꜱᴇ /reload ɪɴ ᴛʜᴀᴛ ɢʀᴏᴜᴘ ᴀɴᴅ ɪᴛ ᴡɪʟʟ ᴀᴘᴘᴇᴀʀ ʜᴇʀᴇ.",
            reply_markup=InlineKeyboardMarkup(group_list)
        )

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer(script.NT_ADMIN_ALRT_TXT, show_alert=True)
            return
        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
            await query.answer("ᴏꜰꜰ ✗")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("ᴏɴ ✓")
        settings = await get_settings(int(grp_id))
        if settings is not None:
            btn = await group_setting_buttons(int(grp_id))
            await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
    await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()

    async def _schedule_delete(sent_obj, orig_msg, delay):
        try:
            await asyncio.sleep(delay)
            try:
                await sent_obj.delete()
            except Exception:
                pass
            try:
                await orig_msg.delete()
            except Exception:
                pass
        except Exception:
            pass

    m = None
    try:
        if not spoll:
            message = msg
            if message.text.startswith("/"):
                return
            if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
                return
            if len(message.text) < 100:
                message_text = message.text or ""
                search = message_text.lower()
                m = await message.reply_text(script.SEARCHING_TXT.format(search))
                find = search.split(" ")
                search = ""
                removes = ["in", "upload", "series", "full", "horror", "thriller", "mystery", "print", "file"]
                for x in find:
                    if x in removes:
                        continue
                    else:
                        search = search + x + " "
                search = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|bro|bruh|broh|helo|that|find|dubbed|link|venum|iruka|pannunga|pannungga|anuppunga|anupunga|anuppungga|anupungga|film|undo|kitti|kitty|tharu|kittumo|kittum|movie|any(one)|with\ssubtitle(s)?)\b", "", search, flags=re.IGNORECASE)
                search = search.replace("-", " ")
                search = re.sub(r"[:']", "", search)
                search = re.sub(r"\s+", " ", search).strip()
                files, offset, total_results = await get_search_results(message.chat.id, search, offset=0, filter=True)
                settings = await get_settings(message.chat.id)
                if not files:
                    if settings.get("spell_check"):
                        ai_sts = await m.edit('🤖 ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ, ᴀɪ ɪꜱ ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...')
                        is_misspelled = await ai_spell_check(chat_id=message.chat.id, wrong_name=search)
                        if is_misspelled:
                            await ai_sts.edit(f'✅ Aɪ Sᴜɢɢᴇsᴛᴇᴅ: <code>{is_misspelled}</code>\n🔍 Searching for it...')
                            message.text = is_misspelled
                            await ai_sts.delete()
                            return await auto_filter(client, message)
                        await ai_sts.delete()
                        return await advantage_spell_chok(client, message)
                    else:
                        try:
                            if m:
                                await m.delete()
                        except Exception:
                            pass
                        return await advantage_spell_chok(client, message)
            else:
                return
        else:
            try:
                message = msg.message.reply_to_message
                if message is None:
                    message = msg.message
                search, files, offset, total_results = spoll
                try:
                    m = await message.reply_text(f'🔎 sᴇᴀʀᴄʜɪɴɢ {search}')
                except AttributeError:
                    m = await msg.message.reply_text(f'🔎 sᴇᴀʀᴄʜɪɴɢ {search}')
                settings = await get_settings(message.chat.id)
                try:
                    await msg.message.delete()
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error in spoll path: {e}", exc_info=True)
                try:
                    message = msg.message
                    search, files, offset, total_results = spoll
                    m = await message.reply_text(f'🔎 sᴇᴀʀᴄʜɪɴɢ {search}')
                    settings = await get_settings(message.chat.id)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    return

        key = f"{message.chat.id}-{message.id}"
        FRESH[key] = search
        temp.GETALL[key] = files
        req = message.from_user.id if message.from_user else 0
        temp.SHORT[message.from_user.id] = message.chat.id
        try:
            await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji="🍿")
        except Exception:
            pass

        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(file.file_name), callback_data=f'file#{file.file_id}'),
                ]
                for file in files
            ]
            btn.insert(0, [
                InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
            ])
            btn.insert(0, [
                InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
            ])
        else:
            btn = [
                [
                    InlineKeyboardButton('𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton("𝐒ᴇᴀsᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                ],
                [
                    InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
                ]
            ]

        if offset != "":
            req = message.from_user.id if message.from_user else 0
            if ULTRA_FAST_MODE:
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(text="1", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                    InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
            else:
                try:
                    if settings['max_btn']:
                        btn.append([
                            InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                            InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                        ])
                    else:
                        max_b = int(MAX_B_TN)
                        btn.append([
                            InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/max_b)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                            InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                        ])
                except KeyError:
                    await save_group_settings(message.chat.id, 'max_btn', True)
                    btn.append([
                        InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER),
                        InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                        InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                    ])
        else:
            btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages")])

        if settings.get('imdb'):
            imdb_poster = await get_posterx(search, file=(files[0]).file_name) if TMDB_POSTER else await get_poster(search, file=(files[0]).file_name)
        else:
            imdb_poster = None

        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())

        TEMPLATE = settings.get('template') or script.IMDB_TEMPLATE_TXT

        if imdb_poster:
            cap = TEMPLATE.format(
                query=search,
                title=imdb_poster['title'],
                votes=imdb_poster['votes'],
                aka=imdb_poster["aka"],
                seasons=imdb_poster["seasons"],
                box_office=imdb_poster['box_office'],
                localized_title=imdb_poster['localized_title'],
                kind=imdb_poster['kind'],
                imdb_id=imdb_poster["imdb_id"],
                cast=imdb_poster['cast'],
                runtime=imdb_poster['runtime'],
                countries=imdb_poster['countries'],
                certificates=imdb_poster['certificates'],
                languages=imdb_poster['languages'],
                director=imdb_poster['director'],
                writer=imdb_poster['writer'],
                producer=imdb_poster['producer'],
                composer=imdb_poster['composer'],
                cinematographer=imdb_poster['cinematographer'],
                music_team=imdb_poster['music_team'],
                distributors=imdb_poster['distributors'],
                release_date=imdb_poster['release_date'],
                year=imdb_poster['year'],
                genres=imdb_poster['genres'],
                poster=imdb_poster['poster'],
                plot=imdb_poster['plot'] if settings.get('button') else "N/A",
                rating=imdb_poster['rating'],
                url=imdb_poster['url'],
                **locals()
            )
            temp.IMDB_CAP[message.from_user.id] = cap
            if not settings.get('button'):
                cap += "\n\n<b><u>Your Requested Files Are Here</u></b>\n\n"
                for idx, file in enumerate(files, start=1):
                    cap += f"\n📀 <b>{get_size(file.file_size)}</b>\n╰⌯⌲ 📁 <b><a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{clean_filename(file.file_name)}</a></b>\n"
        else:
            temp.IMDB_CAP[message.from_user.id] = None
            if ULTRA_FAST_MODE:
                cap = f"<b>🏷 ᴛɪᴛʟᴇ : <code>{search}</code>\n⏰ ʀᴇsᴜʟᴛ ɪɴ : <code>{remaining_seconds} Sᴇᴄᴏɴᴅs</code>\n\n🗳 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n⚜️ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : ⚡ {message.chat.title or temp.B_LINK or 'ᴅʀᴇᴀᴍxʙᴏᴛᴢ'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"
                if not settings.get('button'):
                    for idx, file in enumerate(files, start=1):
                        cap += f"\n📀 <b>{get_size(file.file_size)}</b>\n╰⌯⌲ 📁 <b><a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{clean_filename(file.file_name)}</a></b>\n"
            else:
                cap = f"<b>🏷 ᴛɪᴛʟᴇ : <code>{search}</code>\n🧱 ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ : <code>{total_results}</code>\n⏰ ʀᴇsᴜʟᴛ ɪɴ : <code>{remaining_seconds} Sᴇᴄᴏɴᴅs</code>\n\n📝 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n⚜️ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : ⚡ {message.chat.title or temp.B_LINK or 'ᴅʀᴇᴀᴍxʙᴏᴛᴢ'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"
                if not settings.get('button'):
                    for idx, file in enumerate(files, start=1):
                        cap += f"\n📀 <b>{get_size(file.file_size)}</b>\n╰⌯⌲ 📁 <b><a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{clean_filename(file.file_name)}</a></b>\n"

        try:
            if imdb_poster and imdb_poster.get('poster'):
                try:
                    if TMDB_POSTER:
                        photo = imdb_poster.get('backdrop') if imdb_poster.get('backdrop') and LANDSCAPE_POSTER else imdb_poster.get('poster')
                    else:
                        photo = imdb_poster.get('poster')
                    sent = await message.reply_photo(photo=photo, caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    if m:
                        await m.delete()
                except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                    pic = imdb_poster.get('poster')
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    sent = await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    if m:
                        await m.delete()
                except Exception as e:
                    logger.exception(e)
                    sent = await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
            else:
                sent = await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
                if m:
                    await m.delete()
        except Exception as e:
            logger.exception("Failed to send result: %s", e)
            return

        try:
            if settings.get('auto_delete'):
                asyncio.create_task(_schedule_delete(sent, message, DELETE_TIME))
        except KeyError:
            try:
                await save_group_settings(message.chat.id, 'auto_delete', True)
            except Exception:
                pass
            asyncio.create_task(_schedule_delete(sent, message, DELETE_TIME))
        return

    except Exception as e:
        logger.exception(e)
        return


async def ai_spell_check(chat_id, wrong_name):
    async def search_movie(w_name):
        search_results = imdb.search_movie(w_name)
        if not search_results or not hasattr(search_results, "titles"):
            return []
        return [movie.title for movie in search_results.titles]

    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return
        movie = closest_match[0]
        files, _, _ = await get_search_results(chat_id=chat_id, query=movie)
        if files:
            return movie
        movie_list.remove(movie)


async def advantage_spell_chok(client, message):
    search = message.text
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"

    try:
        movies = await get_poster(search, bulk=True)
    except Exception as e:
        logger.exception("get_poster failed for query=%s: %s", query, e)
        try:
            k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
            await asyncio.sleep(60)
            try:
                await k.delete()
            except Exception:
                pass
        except Exception:
            pass
        try:
            await message.delete()
        except Exception:
            pass
        return

    if not movies:
        button = [[InlineKeyboardButton("ʀᴇǫᴜᴇsᴛ 📝 ᴀᴅᴍɪɴ", url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        try:
            await k.delete()
        except Exception:
            pass
        try:
            await message.delete()
        except Exception:
            pass
        return

    user = message.from_user.id if message.from_user else 0
    buttons = []
    for movie in movies:
        safe_title = movie.title.replace("#", "").replace("\n", " ").strip()[:40]
        if not safe_title:
            safe_title = movie.title[:40]
        buttons.append([InlineKeyboardButton(text=movie.title, callback_data=f"spol#{safe_title}#{user}")])

    buttons.append([InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data', style=enums.ButtonStyle.DANGER)])
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons))
    await asyncio.sleep(60)
    try:
        await d.delete()
    except Exception:
        pass
    try:
        await message.delete()
    except Exception:
        pass
