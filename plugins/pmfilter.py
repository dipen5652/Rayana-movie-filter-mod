from utils import get_random_mix_id, get_size, is_subscribed, is_req_subscribed, group_setting_buttons, get_poster, get_posterx, temp, get_settings, save_group_settings, get_cap, imdb, is_check_admin, extract_request_content, log_error, clean_filename, generate_season_variations, clean_search_text, get_settings_text
from rapidfuzz import process
from dreamxbotz.util.file_properties import get_name, get_hash
from urllib.parse import quote_plus
import logging
import hashlib
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


@Client.on_message(filters.group & filters.text & filters.incoming & ~filters.regex(r"^/") )
async def give_filter(client, message):
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception:
            await message.react(emoji="⚡️")
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
            await message.react(emoji="⚡️")
            pass
    
    if content.startswith(("#")):
        return
    
    try:
        await mdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        
        if pm_search:
            # PM Search enabled - করতে পারবে search
            await auto_filter(bot, message)
        else:
            # PM Search disabled - মেসেজ দেখাবে
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
                # Fallback message
                try:
                    await message.reply_text(
                        f"<b>🙋 Hey {user},\n\n"
                        "ʏᴏᴜ ᴄᴀɴ sᴇᴀʀᴄʜ ᴏɴʟʏ ɪɴ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ!\n\n"
                        "📝 ᴘʟᴇᴀsᴇ ʀᴇǫᴜᴇsᴛ ɪɴ: {}</b>".format(GRP_LNK),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⚝ ᴍɪss ᴘʀᴏᴠɪᴅᴇʀ ʀᴇǫᴜᴇsᴛ ⚝", url=GRP_LNK)]
                        ])
                    )
                except Exception as e2:
                    logger.error(f"❌ Fallback message also failed: {e2}")
            
            # Log করুন
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
        InlineKeyboardButton(
            'invite link', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(
            f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
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

    # RESTART RESILIENCE FIX: Agar bot restart ho chuka ho aur memory khali ho
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        if match:
            search = match.group(1).strip()
            FRESH[key] = search
        else:
            # Fallback agar user title header me kisi aur layout se aaya ho
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
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           "🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)

                   ]
                   )

    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0, [
            InlineKeyboardButton("🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
        ])
    if ULTRA_FAST_MODE:
        if 0 < offset <= 10:
            off_set = 0
        elif offset == 0:
            off_set = None
        else:
            off_set = offset - 10
        if n_offset == 0:
            btn.append(
                [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages")]
            )
        elif off_set is None:
            btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
        else:
            btn.append(
                [
                    InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.SUCCESS)
                ],
            )
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
                    btn.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.DANGER)])
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton(
                                "⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(
                                f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                            InlineKeyboardButton(
                                "ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                        ],
                    )
            else:
                if 0 < offset <= int(MAX_B_TN):
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - int(MAX_B_TN)
                if n_offset == 0:
                    btn.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.SUCCESS)])
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton(
                                "⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(
                                f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                            InlineKeyboardButton(
                                "ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                        ],
                    )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY)]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
            else:
                btn.append(
                    [
                        InlineKeyboardButton(
                            "⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                        InlineKeyboardButton(
                            f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton(
                            "ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
                    ],
                )
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(
                curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        dreamx_title = clean_search_text(search)
        cap = None
        try:
            if settings['imdb']:
                cap = await get_cap(settings, remaining_seconds, files, query, total, dreamx_title, offset)
                if query.message.caption:
                    try:
                        await query.message.edit_caption(caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    except (MessageNotModified, MessageIdInvalid):
                        pass
                    except Exception as e:
                        logger.exception(e)
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
    # FIX 2: Get title directly from button text - NO TMDB API dependency
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
                logger.error("Error In Spol: %s — Make Sure Bot Admin BIN CHANNEL", e)
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("ʀᴇǫᴜᴇsᴛ 📝 ᴀᴅᴍɪɴ", url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)]])
        try:
            k = await query.message.edit_text(text=script.MVE_NT_FND.format(movie_title), reply_markup=btn)
            await asyncio.sleep(10)
            await k.delete()
        except Exception:
            pass

# Qualities
@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\n"
                f"ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""

    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace(' ', '_')

    btn = []
    for i in range(0, len(QUALITIES), 2):
        q1 = QUALITIES[i]
        row = [InlineKeyboardButton(
            text=q1, callback_data=f"fq#{q1.lower()}#{req}#{key}")]
        if i + 1 < len(QUALITIES):
            q2 = QUALITIES[i + 1]
            row.append(InlineKeyboardButton(
                text=q2, callback_data=f"fq#{q2.lower()}#{req}#{key}"))
        btn.append(row)

    btn.insert(0, [
        InlineKeyboardButton(text="⇊ ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ⇊", callback_data="ident", style=enums.ButtonStyle.PRIMARY)
    ])
    btn.append([
        InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭",
                             callback_data=f"fq#homepage#{req}#{key}", style=enums.ButtonStyle.SUCCESS)
    ])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    _, qual, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace("_", " ")
    baal = qual in search
    if baal:
        search = search.replace(qual, "")
    else:
        search = search
    chat_id = query.message.chat.id
    message = query.message
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True,)
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
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
    [
        InlineKeyboardButton(
            "🗃️ Sᴇɴᴅ Aʟʟ 🗃️",
            callback_data=f"sendfiles#{key}",
            style=enums.ButtonStyle.SUCCESS
        )
    ])
    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           "🗃️ Sᴇɴᴅ Aʟʟ 🗃️", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)

                   ])
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(

                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                )
            else:
                btn.append(

                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(

                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
            )
    else:
        btn.append(

            [InlineKeyboardButton(
                text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.DANGER)]
        )
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(
                curr_time.second+(curr_time.microsecond/1000000)))
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

# languages


@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\n"
                f"ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace(' ', '_')

    items = list(LANGUAGES.items())
    btn = []

    for i in range(0, len(items), 2):
        name1, code1 = items[i]
        row = [InlineKeyboardButton(
            text=name1, callback_data=f"fl#{code1}#{req}#{key}")]
        if i + 1 < len(items):
            name2, code2 = items[i + 1]
            row.append(InlineKeyboardButton(
                text=name2, callback_data=f"fl#{code2}#{req}#{key}"))
        btn.append(row)

    btn.insert(0, [InlineKeyboardButton(
        text="⇊ ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ ⇊", callback_data="ident", style=enums.ButtonStyle.SUCCESS)])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭",
               callback_data=f"fl#homepage#{req}#{key}", style=enums.ButtonStyle.PRIMARY)])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
        search = match.group(1).strip() if match else ""
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = search.replace("_", " ")
    baal = lang in search
    if baal:
        search = search.replace(lang, "")
    else:
        search = search
    chat_id = query.message.chat.id
    message = query.message
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True,)
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
                InlineKeyboardButton(text=f"{get_size(file.file_size)} ≽ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        [
    InlineKeyboardButton(
        "🗃️ Sᴇɴᴅ Aʟʟ 🗃️",
        callback_data=f"sendfiles#{key}",
        style=enums.ButtonStyle.SUCCESS
    )
        ]
    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           '𝐐ᴜᴀʟɪᴛʏ', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "𝐒ᴇᴀsᴏɴ",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        [
    InlineKeyboardButton(
        "🗃️ Sᴇɴᴅ Aʟʟ 🗃️",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
        ]
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [
                        InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                            text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                    ])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.FANGER), InlineKeyboardButton(
                            text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                    ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
    else:
        btn.append([InlineKeyboardButton(
            text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.PRIMARY)])
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(
                curr_time.second+(curr_time.microsecond/1000000)))
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
    btn: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(SEASONS) - 1, 2):
        btn.append([
            InlineKeyboardButton(
                f"𝐒ᴇᴀꜱᴏɴ {SEASONS[i][1:]}", callback_data=f"fs#{SEASONS[i].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton(
                f"𝐒ᴇᴀꜱᴏɴ {SEASONS[i+1][1:]}", callback_data=f"fs#{SEASONS[i+1].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])

    btn.insert(
        0,
        [InlineKeyboardButton("⇊ ꜱᴇʟᴇᴄᴛ ꜱᴇᴀꜱᴏɴ ⇊", callback_data="ident", style=enums.ButtonStyle.SUCCESS)],
    )
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ​↭",
               callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.PRIMARY)])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_seasons_cb_handler(client: Client, query: CallbackQuery):
    start_t = datetime.now(pytz.timezone("Asia/Kolkata"))
    _, season_tag, req, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        raw_text = query.message.caption or query.message.text or ""
        match = re.search(r"🏷\s*(?:ᴛɪᴛʟᴇ|TITLE)\s*:\s*<code>(.*?)</code>", raw_text, re.IGNORECASE)
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
    btn: list[list[InlineKeyboardButton]] = []
    if settings.get("button"):
        btn.extend(
            [
                [
                    InlineKeyboardButton(
                        f"{get_size(f.file_size)} ≽ " +
                        clean_filename(f.file_name),
                        callback_data=f"file#{f.file_id}",
                    )
                ]
                for f in files
            ]
        )
    btn.insert(
        0,
        [
            InlineKeyboardButton("𝐐ᴜᴀʟɪᴛʏ", callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("𝐋ᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝐒ᴇᴀꜱᴏɴ", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER),
        ],
    )
    [
    InlineKeyboardButton(
        "🗃️ Sᴇɴᴅ Aʟʟ 🗃️",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
    ]
    if n_offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
                )

            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
            )
    else:
        n_offset = 0
        btn.append(
            [InlineKeyboardButton(
                "↭  ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages", style=enums.ButtonStyle.PRIMARY)]
        )
    if not settings.get("button"):
        time_difference = datetime.now(pytz.timezone("Asia/Kolkata")) - start_t
        remaining_seconds = f"{time_difference.total_seconds():.2f}"
        dreamx_title = clean_search_text(search_final)
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, dreamx_title, offset=1)
        try:
            await query.message.edit_text(
                text=cap,
                reply_markup=InlineKeyboardMarkup(btn),
            )
        except (MessageNotModified, MessageIdInvalid):
            pass
    else:
        try:
            await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
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
        await query.answer("ᴛʜɪs ɪs ᴘᴀɢᴇs ʙᴜᴛᴛᴏɴ ʙꜱᴅᴋ 😅")



    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = query.message.reply_to_message.from_user.id if query.message.reply_to_message else query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")

    elif query.data.startswith("sendfiles"):
        ident, key = query.data.split("#")
        settings = await get_settings(query.message.chat.id)
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
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if not result.deleted_count and MULTIPLE_DB:
                        result = await Media2.collection.delete_one({
                            '_id': file_ids,
                        })
                    if result.deleted_count:
                        logger.info(
                            f'ꜰɪʟᴇ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}! ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀꜱᴇ.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ ᴅᴇʟᴇᴛɪɴɢ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ. ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword} !\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.error("Error In killfiledq: %s", e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜰᴏʀ ꜰɪʟᴇ ᴅᴇʟᴇᴛᴀᴛɪᴏɴ !\n\nꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}.</b>")

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
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=await get_settings_text(grp_id, title),
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)

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
        btn2 = [[
            InlineKeyboardButton(
                "ᴄʜᴇᴄᴋ ᴍʏ ᴅᴍ 🗳️", url=f"telegram.me/{temp.U_NAME}", style=enums.ButtonStyle.SUCCESS)
        ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ ғᴏʀ {title} ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            btn = await group_setting_buttons(int(grp_id))
            reply_markup = InlineKeyboardMarkup(btn)
            await client.send_message(
                chat_id=userid,
                text=await get_settings_text(grp_id, title),
                reply_markup=reply_markup,
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
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
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
                "sup": "<b>Hᴇʏ {mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
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
                "sup": "<b>Hᴇʏ {mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n#Aᴠᴀɪʟᴀʙʟᴇ 💗\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢES.</small></i>",
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
                    logger.error("Neither BIN_CHANNEL nor LOG_CHANNEL is valid.")
                    try:
                        await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file_id,
                            caption="✅ <b>Here is your file directly!</b>\n\n⚠️ <i>Admin Note: BIN_CHANNEL/LOG_CHANNEL is not set with -100 ID in .env.</i>"
                        )
                        await query.answer("✅ Sent file directly to your PM!\n(Stream requires valid channel setup)", show_alert=True)
                        return
                    except Exception as fallback_err:
                        logger.error("Direct send failed: %s", fallback_err)
                        await query.answer("⚠️ BIN_CHANNEL / LOG_CHANNEL is not configured!\nAdd bot as Admin with -100 ID in .env.", show_alert=True)
                        return

            user_id = query.from_user.id
            username = query.from_user.mention if query.from_user else f"User {user_id}"
            log_msg = None

            # 1. Attempt to
