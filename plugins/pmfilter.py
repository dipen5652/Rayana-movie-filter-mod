from utils import get_random_mix_id, get_size, is_subscribed, is_req_subscribed, group_setting_buttons, get_poster, get_posterx, temp, get_settings, save_group_settings, get_cap, imdb, is_check_admin, extract_request_content, log_error, clean_filename, generate_season_variations, clean_search_text, get_settings_text
from rapidfuzz import process
from dreamxbotz.util.file_properties import get_name, get_hash
from urllib.parse import quote_plus
import logging
from database.ia_filterdb import Media, Media2, get_search_results, get_bad_files
from database.config_db import mdb
from pyrogram.errors import MessageIdInvalid, UserIsBlocked, MessageNotModified, PeerIdInvalid
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
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
            await message.react(emoji="âš¡ï¸")
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
                [[InlineKeyboardButton("ðŸ” á´Šá´ÉªÉ´ á´€É´á´… êœ±á´‡á´€Ê€á´„Êœ Êœá´‡Ê€á´‡ ðŸ”Ž", url=GRP_LNK)]])
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
            await message.react(emoji="âš¡ï¸")
            pass
    
    if content.startswith(("#")):
        return
    
    try:
        await mdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        
        if pm_search:
            # PM Search enabled - à¦•à¦°à¦¤à§‡ à¦ªà¦¾à¦°à¦¬à§‡ search
            await auto_filter(bot, message)
        else:
            # PM Search disabled - à¦®à§‡à¦¸à§‡à¦œ à¦¦à§‡à¦–à¦¾à¦¬à§‡
            logger.info(f"ðŸš« PM Search Disabled For User: {user_id}")
            
            try:
                await message.reply_text(
                    text=script.PM_SEARCH_DISABLED_TXT.format(user=user),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("âš á´Éªss á´˜Ê€á´á´ Éªá´…á´‡Ê€ Ê€á´‡Ç«á´œá´‡sá´› âš", url=GRP_LNK)]
                    ])
                )
            except Exception as e:
                logger.error(f"âŒ Failed to send PM_SEARCH_DISABLED message: {e}")
                # Fallback message
                try:
                    await message.reply_text(
                        f"<b>ðŸ™‹ Hey {user},\n\n"
                        "Êá´á´œ á´„á´€É´ sá´‡á´€Ê€á´„Êœ á´É´ÊŸÊ ÉªÉ´ sá´œá´˜á´˜á´Ê€á´› É¢Ê€á´á´œá´˜!\n\n"
                        "ðŸ“ á´˜ÊŸá´‡á´€sá´‡ Ê€á´‡Ç«á´œá´‡sá´› ÉªÉ´: {}</b>".format(GRP_LNK),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("âš á´Éªss á´˜Ê€á´á´ Éªá´…á´‡Ê€ Ê€á´‡Ç«á´œá´‡sá´› âš", url=GRP_LNK)]
                        ])
                    )
                except Exception as e2:
                    logger.error(f"âŒ Fallback message also failed: {e2}")
            
            # Log à¦•à¦°à§à¦¨
            try:
                await bot.send_message(
                    chat_id=LOG_CHANNEL,
                    text=script.PM_LOG_TXT.format(user, user_id, content)
                )
            except Exception as e:
                logger.error(f"âŒ Failed to log PM message: {e}")
    
    except Exception as e:
        logger.error(f"âŒ Error in pm_text handler: {e}", exc_info=True)


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton(
            'invite link', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(
            f'â³ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
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
                InlineKeyboardButton(text=f"{get_size(file.file_size)} â‰½ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)

                   ]
                   )

    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0, [
            InlineKeyboardButton("ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)
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
                [InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages")]
            )
        elif off_set is None:
            btn.append([InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages"), InlineKeyboardButton("É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}")])
        else:
            btn.append(
                [
                    InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1}", callback_data="pages", style=enums.ButtonStyle.DANGER),
                    InlineKeyboardButton("É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.SUCCESS)
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
                    btn.append([InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.DANGER)])
                elif off_set is None:
                    btn.append([InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages"), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton("É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton(
                                "â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(
                                f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS),
                            InlineKeyboardButton(
                                "É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
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
                    btn.append([InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}, style=enums.ButtonStyle.DANGER"), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.SUCCESS)])
                elif off_set is None:
                    btn.append([InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages, style=enums.ButtonStyle.PRIMARY"), InlineKeyboardButton("É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton(
                                "â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                            InlineKeyboardButton(
                                f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                            InlineKeyboardButton(
                                "É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
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
                    [InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY)]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton("É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)])
            else:
                btn.append(
                    [
                        InlineKeyboardButton(
                            "â‹ž Ê™á´€á´„á´‹", callback_data=f"next_{req}_{key}_{off_set}", style=enums.ButtonStyle.DANGER),
                        InlineKeyboardButton(
                            f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton(
                            "É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)
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
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movies = await get_posterx(id, id=True) if TMDB_ON_SEARCH else await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            try:
                await bot.send_message(chat_id=BIN_CHANNEL, text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
            except Exception as e:
                logger.error("Error In Spol: %s â€” Make Sure Bot Admin BIN CHANNEL", e)
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Ê€á´‡Ç«á´œá´‡sá´› ðŸ“ á´€á´…á´ÉªÉ´", url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)]])
        k = await query.message.edit(script.MVE_NT_FND, reply_markup=btn)
        await asyncio.sleep(10)
        await k.delete()

# Qualities
@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    _, req, key = query.data.split("#")
    try:
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(
                f"âš ï¸ Êœá´‡ÊŸÊŸá´ {query.from_user.first_name},\n"
                f"á´›ÊœÉªêœ± Éªêœ± É´á´á´› Êá´á´œÊ€ á´á´á´ Éªá´‡ Ê€á´‡Ç«á´œá´‡êœ±á´›,\nÊ€á´‡Ç«á´œá´‡êœ±á´› Êá´á´œÊ€'êœ±...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
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
        InlineKeyboardButton(text="â‡Š êœ±á´‡ÊŸá´‡á´„á´› Ç«á´œá´€ÊŸÉªá´›Ê â‡Š", callback_data="ident", style=enums.ButtonStyle.PRIMARY)
    ])
    btn.append([
        InlineKeyboardButton(text="â†­ Ê™á´€á´„á´‹ á´›á´ êœ°ÉªÊŸá´‡s â†­",
                             callback_data=f"fq#homepage#{req}#{key}", style=enums.ButtonStyle.SUCCESS)
    ])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    _, qual, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
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
            return await query.answer(f"âš ï¸ Êœá´‡ÊŸÊŸá´ {query.from_user.first_name},\ná´›ÊœÉªêœ± Éªêœ± É´á´á´› Êá´á´œÊ€ á´á´á´ Éªá´‡ Ê€á´‡Ç«á´œá´‡êœ±á´›,\nÊ€á´‡Ç«á´œá´‡êœ±á´› Êá´á´œÊ€'êœ±...", show_alert=True,)
    except Exception:
        pass
    if qual != "homepage":
        search = f"{search} {qual}"
    BUTTONS[key] = search
    files, offset, total_results = await get_search_results(chat_id, search, offset=0, filter=True)
    if not files:
        await query.answer("ðŸš« É´á´ êœ°ÉªÊŸá´‡êœ± á´¡á´‡Ê€á´‡ êœ°á´á´œÉ´á´… ðŸš«", show_alert=1)
        return
    temp.GETALL[key] = files
    settings = await get_settings(message.chat.id)
    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(text=f"{get_size(file.file_size)} â‰½ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
    [
        InlineKeyboardButton(
            "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
            callback_data=f"sendfiles#{key}",
            style=enums.ButtonStyle.SUCCESS
        )
    ])
    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸", callback_data=f"sendfiles#{key}", style=enums.ButtonStyle.SUCCESS)

                   ])
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(

                    [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                )
            else:
                btn.append(

                    [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(

                [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
            )
    else:
        btn.append(

            [InlineKeyboardButton(
                text="â†­ É´á´ á´á´Ê€á´‡ á´˜á´€É¢á´‡êœ± á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â†­", callback_data="pages", style=enums.ButtonStyle.DANGER)]
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
                f"âš ï¸ Êœá´‡ÊŸÊŸá´ {query.from_user.first_name},\n"
                f"á´›ÊœÉªêœ± Éªêœ± É´á´á´› Êá´á´œÊ€ á´á´á´ Éªá´‡ Ê€á´‡Ç«á´œá´‡êœ±á´›,\nÊ€á´‡Ç«á´œá´‡êœ±á´› Êá´á´œÊ€'êœ±...",
                show_alert=True,
            )
    except Exception:
        pass

    search = FRESH.get(key)
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
        text="â‡Š êœ±á´‡ÊŸá´‡á´„á´› ÊŸá´€É´É¢á´œá´€É¢á´‡ â‡Š", callback_data="ident", style=enums.ButtonStyle.SUCCESS)])
    btn.append([InlineKeyboardButton(text="â†­ Ê™á´€á´„á´‹ á´›á´ êœ°ÉªÊŸá´‡s â†­",
               callback_data=f"fl#homepage#{req}#{key}", style=enums.ButtonStyle.PRIMARY)])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, req, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
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
            return await query.answer(f"âš ï¸ Êœá´‡ÊŸÊŸá´ {query.from_user.first_name},\ná´›ÊœÉªêœ± Éªêœ± É´á´á´› Êá´á´œÊ€ á´á´á´ Éªá´‡ Ê€á´‡Ç«á´œá´‡êœ±á´›,\nÊ€á´‡Ç«á´œá´‡êœ±á´› Êá´á´œÊ€'êœ±...", show_alert=True,)
    except Exception:
        pass
    if lang != "homepage":
        search = f"{search} {lang}"
    BUTTONS[key] = search
    files, offset, total_results = await get_search_results(chat_id, search, offset=0, filter=True)
    if not files:
        await query.answer("ðŸš« É´á´ êœ°ÉªÊŸá´‡êœ± á´¡á´‡Ê€á´‡ êœ°á´á´œÉ´á´… ðŸš«", show_alert=1)
        return
    temp.GETALL[key] = files
    settings = await get_settings(message.chat.id)
    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(text=f"{get_size(file.file_size)} â‰½ " + clean_filename(
                    file.file_name), callback_data=f'file#{file.file_id}'),
            ]
            for file in files
        ]
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        [
    InlineKeyboardButton(
        "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
        callback_data=f"sendfiles#{key}",
        style=enums.ButtonStyle.SUCCESS
    )
        ]
    else:
        btn = []
        btn.insert(0,
                   [
                       InlineKeyboardButton(
                           'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                       InlineKeyboardButton(
                           "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                       InlineKeyboardButton(
                           "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                   ]
                   )
        [
    InlineKeyboardButton(
        "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
        ]
    if offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [
                        InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                            text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                    ])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.FANGER), InlineKeyboardButton(
                            text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                    ])
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [
                    InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.PRIMARY), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)
                ])
    else:
        btn.append([InlineKeyboardButton(
            text="â†­ É´á´ á´á´Ê€á´‡ á´˜á´€É¢á´‡êœ± á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â†­", callback_data="pages", style=enums.ButtonStyle.PRIMARY)])
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
                f"âš ï¸ Êœá´‡ÊŸÊŸá´Â {query.from_user.first_name},\ná´›ÊœÉªêœ±Â Éªêœ±Â É´á´á´›Â Êá´á´œÊ€Â á´á´á´ Éªá´‡Â Ê€á´‡Ç«á´œá´‡êœ±á´›,\nÊ€á´‡Ç«á´œá´‡êœ±á´›Â Êá´á´œÊ€'êœ±â€¦",
                show_alert=True,
            )
    except Exception:
        pass
    offset = 0
    btn: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(SEASONS) - 1, 2):
        btn.append([
            InlineKeyboardButton(
                f"ð’á´‡á´€êœ±á´É´ {SEASONS[i][1:]}", callback_data=f"fs#{SEASONS[i].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton(
                f"ð’á´‡á´€êœ±á´É´ {SEASONS[i+1][1:]}", callback_data=f"fs#{SEASONS[i+1].lower()}#{req}#{key}", style=enums.ButtonStyle.DANGER)
        ])

    btn.insert(
        0,
        [InlineKeyboardButton("â‡Š êœ±á´‡ÊŸá´‡á´„á´›Â êœ±á´‡á´€êœ±á´É´ â‡Š", callback_data="ident", style=enums.ButtonStyle.SUCCESS)],
    )
    btn.append([InlineKeyboardButton(text="â†­ Ê™á´€á´„á´‹ á´›á´ êœ°ÉªÊŸá´‡s â€‹â†­",
               callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.PRIMARY)])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_seasons_cb_handler(client: Client, query: CallbackQuery):
    start_t = datetime.now(pytz.timezone("Asia/Kolkata"))
    _, season_tag, req, key = query.data.split("#")
    search = FRESH.get(key).replace("_", " ")
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
            return await query.answer("âš ï¸ Not your request", show_alert=True)
    except Exception:
        pass

    chat_id = query.message.chat.id
    files, n_offset, total_results = await get_search_results(chat_id, query_input, offset=0, filter=True)
    if not files:
        BUTTONS[key] = None
        return await query.answer("ðŸš« É´á´ êœ°ÉªÊŸá´‡êœ± êœ°á´á´œÉ´á´… ðŸš«", show_alert=True)

    temp.GETALL[key] = files
    settings = await get_settings(chat_id)
    btn: list[list[InlineKeyboardButton]] = []
    if settings.get("button"):
        btn.extend(
            [
                [
                    InlineKeyboardButton(
                        f"{get_size(f.file_size)} â‰½ " +
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
            InlineKeyboardButton("ðá´œá´€ÊŸÉªá´›Ê", callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ð’á´‡á´€êœ±á´É´", callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER),
        ],
    )
    [
    InlineKeyboardButton(
        "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
    ]
    if n_offset != "":
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
                )

            else:
                btn.append(
                    [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
                )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                    text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{n_offset}", style=enums.ButtonStyle.DANGER)]
            )
    else:
        n_offset = 0
        btn.append(
            [InlineKeyboardButton(
                "â†­  É´á´ á´á´Ê€á´‡ á´˜á´€É¢á´‡êœ± á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â†­", callback_data="pages", style=enums.ButtonStyle.PRIMARY)]
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
        await query.answer("á´›Êœá´€É´á´‹s êœ°á´Ê€ á´„ÊŸá´sá´‡ ðŸ™ˆ")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass

    elif query.data == "pages":
        await query.answer("á´›ÊœÉªs Éªs á´˜á´€É¢á´‡s Ê™á´œá´›á´›á´É´ Ê™êœ±á´…á´‹ ðŸ˜…")



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
            await query.answer('UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´á´€ÊœÉ´ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")



    elif query.data.startswith("autofilter_delete"):
        await Media.collection.drop()
        if MULTIPLE_DB:    
            await Media2.collection.drop()
        await query.answer("Eá´ á´‡Ê€Êá´›ÊœÉªÉ´É¢'s Gá´É´á´‡")
        await query.message.edit('êœ±á´œá´„á´„á´‡êœ±êœ±êœ°á´œÊŸÊŸÊ á´…á´‡ÊŸá´‡á´›á´‡á´… á´€ÊŸÊŸ ÉªÉ´á´…á´‡xá´‡á´… êœ°ÉªÊŸá´‡êœ± âœ…')

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
                btn.append([InlineKeyboardButton("â™»ï¸ á´›Ê€Ê á´€É¢á´€ÉªÉ´ â™»ï¸", callback_data=f"checksub#{kk}#{file_id}", style=enums.ButtonStyle.PRIMARY)])
                try:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
                except (MessageNotModified, MessageIdInvalid):
                    pass
                await query.answer(
                    f"ðŸ‘‹ Hello {query.from_user.first_name},\n\n"
                    "ðŸ›‘ Yá´á´œ Êœá´€á´ á´‡ É´á´á´› á´Šá´ÉªÉ´á´‡á´… á´€ÊŸÊŸ Ê€á´‡Ç«á´œÉªÊ€á´‡á´… á´œá´˜á´…á´€á´›á´‡ CÊœá´€É´É´á´‡ÊŸs.\n"
                    "ðŸ‘‰ PÊŸá´‡á´€sá´‡ á´Šá´ÉªÉ´ á´‡á´€á´„Êœ á´É´á´‡ á´€É´á´… á´›Ê€Ê á´€É¢á´€ÉªÉ´.\n",
                    show_alert=True
                )
                return
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
            if query.message.chat.type == enums.ChatType.PRIVATE:
                await query.message.delete()
        except Exception as e:
            await log_error(client, f"âŒ Error in checksub callback:\n\n{repr(e)}")
            logger.error(f"âŒ Error in checksub callback:\n\n{repr(e)}")


    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>êœ°ÉªÊŸá´‡ á´…á´‡ÊŸá´‡á´›Éªá´É´ á´˜Ê€á´á´„á´‡êœ±êœ± á´¡ÉªÊŸÊŸ êœ±á´›á´€Ê€á´› ÉªÉ´ 5 êœ±á´‡á´„á´É´á´…êœ± !</b>")
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
                            f'êœ°ÉªÊŸá´‡ êœ°á´á´œÉ´á´… êœ°á´Ê€ Êá´á´œÊ€ Ç«á´œá´‡Ê€Ê {keyword}! êœ±á´œá´„á´„á´‡êœ±êœ±êœ°á´œÊŸÊŸÊ á´…á´‡ÊŸá´‡á´›á´‡á´… {file_name} êœ°Ê€á´á´ á´…á´€á´›á´€Ê™á´€êœ±á´‡.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>á´˜Ê€á´á´„á´‡êœ±êœ± êœ±á´›á´€Ê€á´›á´‡á´… êœ°á´Ê€ á´…á´‡ÊŸá´‡á´›ÉªÉ´É¢ êœ°ÉªÊŸá´‡êœ± êœ°Ê€á´á´ á´…Ê™. êœ±á´œá´„á´„á´‡êœ±êœ±êœ°á´œÊŸÊŸÊ á´…á´‡ÊŸá´‡á´›á´‡á´… {str(deleted)} êœ°ÉªÊŸá´‡êœ± êœ°Ê€á´á´ á´…Ê™ êœ°á´Ê€ Êá´á´œÊ€ Ç«á´œá´‡Ê€Ê {keyword} !\n\ná´˜ÊŸá´‡á´€êœ±á´‡ á´¡á´€Éªá´›...</b>")
            except Exception as e:
                logger.error("Error In killfiledq: %s", e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>á´˜Ê€á´á´„á´‡êœ±êœ± á´„á´á´á´˜ÊŸá´‡á´›á´‡á´… êœ°á´Ê€ êœ°ÉªÊŸá´‡ á´…á´‡ÊŸá´‡á´›á´€á´›Éªá´É´ !\n\nêœ±á´œá´„á´„á´‡êœ±êœ±êœ°á´œÊŸÊŸÊ á´…á´‡ÊŸá´‡á´›á´‡á´… {str(deleted)} êœ°ÉªÊŸá´‡êœ± êœ°Ê€á´á´ á´…Ê™ êœ°á´Ê€ Êá´á´œÊ€ Ç«á´œá´‡Ê€Ê {keyword}.</b>")

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Êá´á´œ á´…á´É´'á´› Êœá´€á´ á´‡ Ê€ÉªÉ¢Êœá´›êœ± á´›á´ á´…á´ á´›ÊœÉªêœ± !", show_alert=True)
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
            await query.answer("Yá´á´œ á´…á´É´'á´› Êœá´€á´ á´‡ sá´œÒ“Ò“Éªá´„Éªá´€É´á´› Ê€ÉªÉ¢Êœá´›s á´›á´ á´…á´ á´›ÊœÉªs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
            InlineKeyboardButton(
                "á´„Êœá´‡á´„á´‹ á´Ê á´…á´ ðŸ—³ï¸", url=f"telegram.me/{temp.U_NAME}", style=enums.ButtonStyle.SUCCESS)
        ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>Êá´á´œÊ€ sá´‡á´›á´›ÉªÉ´É¢s á´á´‡É´á´œ Ò“á´Ê€ {title} Êœá´€s Ê™á´‡á´‡É´ sá´‡É´á´› á´›á´ Êá´á´œ Ê™Ê á´…á´.</b>")
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
            InlineKeyboardButton("âš ï¸ á´œÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âš ï¸", callback_data=f"unavailable#{from_user}"),
            InlineKeyboardButton("ðŸŸ¢ á´œá´˜ÊŸá´á´€á´…á´‡á´… ðŸŸ¢", callback_data=f"uploaded#{from_user}")
        ], [
            InlineKeyboardButton("â™»ï¸ á´€ÊŸÊ€á´‡á´€á´…Ê á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â™»ï¸", callback_data=f"already_available#{from_user}")
        ], [
            InlineKeyboardButton("ðŸ“Œ Not Released ðŸ“Œ", callback_data=f"Not_Released#{from_user}"),
            InlineKeyboardButton("â™¨ï¸Type Correct Spellingâ™¨ï¸", callback_data=f"Type_Correct_Spelling#{from_user}")
        ], [
            InlineKeyboardButton("âšœï¸ Not Available In The Hindi âšœï¸", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
        ]]
        if query.from_user.id in ADMINS:
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Há´‡Ê€á´‡ á´€Ê€á´‡ á´›Êœá´‡ á´á´˜á´›Éªá´É´s !")
        else:
            await query.answer("Yá´á´œ á´…á´É´'á´› Êœá´€á´ á´‡ sá´œÒ“Ò“Éªá´„Éªá´€É´á´› Ê€ÉªÉ¢Êœá´›s á´›á´ á´…á´ á´›ÊœÉªs !", show_alert=True)

    elif query.data.split("#")[0] in ["unavailable", "Not_Released", "Type_Correct_Spelling", "Not_Available_In_The_Hindi", "uploaded", "already_available"]:
        key = query.data.split("#")[0]
        ident, from_user = query.data.split("#")
        if query.from_user.id not in ADMINS:
            return await query.answer("Yá´á´œ á´…á´É´'á´› Êœá´€á´ á´‡ sá´œÒ“Ò“Éªá´„Éªá´€É´á´› Ê€ÉªÉ¢Êœá´›s á´›á´ á´…á´ á´›ÊœÉªs !", show_alert=True)
            
        status_configs = {
            "unavailable": {
                "btn_text": "âš ï¸ á´œÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âš ï¸", "alert_key": "unalert", "answer": "Sá´‡á´› á´›á´ UÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ !",
                "pm": "<b>Há´‡Ê {mention},</b>\n\n<u>{content}</u> Há´€s Bá´‡á´‡É´ Má´€Ê€á´‹á´‡á´… Aá´… á´œÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡...ðŸ’”\n\n#UÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âš ï¸",
                "sup": "<b>Há´‡Ê {mention},</b>\n\n<u>{content}</u> Há´€s Bá´‡á´‡É´ Má´€Ê€á´‹á´‡á´… Aá´… á´œÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡...ðŸ’”\n\n#UÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âš ï¸\n\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ±.</small></b>",
                "search": False
            },
            "Not_Released": {
                "btn_text": "ðŸ“Œ Not Released ðŸ“Œ", "alert_key": "nralert", "answer": "Sá´‡á´› á´›á´ Ná´á´› Rá´‡ÊŸá´‡á´€êœ±á´‡á´… !",
                "pm": "<b>Há´‡Ê {mention}\n\n<code>{content}</code>, Êá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Êœá´€êœ± É´á´á´› Ê™á´‡á´‡É´ Ê€á´‡ÊŸá´‡á´€êœ±á´‡á´… Êá´‡á´›\n\n#Cá´á´ÉªÉ´É¢Sá´á´É´...ðŸ•Šï¸âœŒï¸</b>",
                "sup": "<u>Há´‡Ê {mention}</u>\n\n<b><code>{content}</code>, Êá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Êœá´€êœ± É´á´á´› Ê™á´‡á´‡É´ Ê€á´‡ÊŸá´‡á´€êœ±á´‡á´… Êá´‡á´›\n\n#Cá´á´ÉªÉ´É¢Sá´á´É´...ðŸ•Šï¸âœŒï¸\n\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ±.</small></b>",
                "search": False
            },
            "Type_Correct_Spelling": {
                "btn_text": "â™¨ï¸ Type Correct Spelling â™¨ï¸", "alert_key": "wsalert", "answer": "Sá´‡á´› á´›á´ Cá´Ê€Ê€á´‡á´„á´› Sá´˜á´‡ÊŸÊŸÉªÉ´É¢ !",
                "pm": "<b>Há´‡Ê {mention}\n\nWá´‡ Dá´‡á´„ÊŸÉªÉ´á´‡á´… Yá´á´œÊ€ Rá´‡Ç«á´œá´‡sá´› <code>{content}</code>, Bá´‡á´„á´€á´œsá´‡ Yá´á´œÊ€ Sá´˜á´‡ÊŸÊŸÉªÉ´É¢ Wá´€s WÊ€á´É´É¢ ðŸ˜¢\n\n#WÊ€á´É´É¢_Sá´˜á´‡ÊŸÊŸÉªÉ´É¢ ðŸ˜‘</b>",
                "sup": "<u>Há´‡Ê {mention}</u>\n\n<b><code>{content}</code>, Bá´‡á´„á´€á´œsá´‡ Yá´á´œÊ€ Sá´˜á´‡ÊŸÊŸÉªÉ´É¢ Wá´€s WÊ€á´É´É¢ ðŸ˜¢\n\n#WÊ€á´É´É¢_Sá´˜á´‡ÊŸÊŸÉªÉ´É¢ ðŸ˜‘\n\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ±.</small></b>",
                "search": False
            },
            "Not_Available_In_The_Hindi": {
                "btn_text": "âšœï¸ Not Available In The Hindi âšœï¸", "alert_key": "hnalert", "answer": "Sá´‡á´› á´›á´ Ná´á´› Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ IÉ´ HÉªÉ´á´…Éª !",
                "pm": "<b>Há´‡Ê {mention}\n\nYá´á´œÊ€ Rá´‡Ç«á´œá´‡sá´› <code>{content}</code> Éªs Ná´á´› Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ÉªÉ´ HÉªÉ´á´…Éª Ê€ÉªÉ¢Êœá´› É´á´á´¡. Sá´ á´á´œÊ€ á´á´á´…á´‡Ê€á´€á´›á´Ê€s á´„á´€É´'á´› á´œá´˜ÊŸá´á´€á´… Éªá´›\n\n#HÉªÉ´á´…Éª_É´á´á´›_á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âŒ</b>",
                "sup": "<u>Há´‡Ê {mention}</u>\n\n<b><code>{content}</code> Éªs Ná´á´› Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ÉªÉ´ HÉªÉ´á´…Éª Ê€ÉªÉ¢Êœá´› É´á´á´¡. Sá´ á´á´œÊ€ á´á´á´…á´‡Ê€á´€á´›á´Ê€s á´„á´€É´'á´› á´œá´˜ÊŸá´á´€á´… Éªá´›\n\n#HÉªÉ´á´…Éª_É´á´á´›_á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âŒ\n\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ±.</small></b>",
                "search": False
            },
            "uploaded": {
                "btn_text": "ðŸŸ¢ á´œá´˜ÊŸá´á´€á´…á´‡á´… ðŸŸ¢", "alert_key": "upalert", "answer": "Sá´‡á´› á´›á´ Uá´˜ÊŸá´á´€á´…á´‡á´… !",
                "pm": "<b>Há´‡Ê {mention},\n\n<u>{content}</u> Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Êœá´€êœ± Ê™á´‡á´‡É´ á´œá´˜ÊŸá´á´€á´…á´‡á´… Ê™Ê á´á´œÊ€ á´á´á´…á´‡Ê€á´€á´›á´Ê€s.\nKÉªÉ´á´…ÊŸÊ sá´‡á´€Ê€á´„Êœ ÉªÉ´ á´á´œÊ€ GÊ€á´á´œá´˜.</b>\n\n#Uá´˜ÊŸá´á´€á´…á´‡á´…âœ…",
                "sup": "<u>{content}</u>\n\n<b>Há´‡Ê {mention}, Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Êœá´€êœ± Ê™á´‡á´‡É´ á´œá´˜ÊŸá´á´€á´…á´‡á´… Ê™Ê á´á´œÊ€ á´á´á´…á´‡Ê€á´€á´›á´Ê€s.KÉªÉ´á´…ÊŸÊ sá´‡á´€Ê€á´„Êœ ÉªÉ´ á´á´œÊ€ GÊ€á´á´œá´˜.</b>\n\n#Uá´˜ÊŸá´á´€á´…á´‡á´…âœ…\n\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ±.</small>",
                "search": True
            },
            "already_available": {
                "btn_text": "â™»ï¸ á´€ÊŸÊ€á´‡á´€á´…Ê á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â™»ï¸", "alert_key": "alalert", "answer": "Sá´‡á´› á´›á´ AÊŸÊ€á´‡á´€á´…Ê Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ !",
                "pm": "<b>Há´‡Ê {mention},\n\n<u>{content}</u> Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Éªêœ± á´€ÊŸÊ€á´‡á´€á´…Ê á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ÉªÉ´ á´á´œÊ€ Ê™á´á´›'êœ± á´…á´€á´›á´€Ê™á´€êœ±á´‡.\nKÉªÉ´á´…ÊŸÊ sá´‡á´€Ê€á´„Êœ ÉªÉ´ á´á´œÊ€ GÊ€á´á´œá´˜.</b>\n\n#Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ðŸ’—",
                "sup": "<b>Há´‡Ê {mention},\n\n<u>{content}</u> Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Éªêœ± á´€ÊŸÊ€á´‡á´€á´…Ê á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ÉªÉ´ á´á´œÊ€ Ê™á´á´›'êœ± á´…á´€á´›á´€Ê™á´€êœ±á´‡.\nKÉªÉ´á´…ÊŸÊ sá´‡á´€Ê€á´„Êœ ÉªÉ´ á´á´œÊ€ GÊ€á´á´œá´˜.</b>\n\n#Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ðŸ’—\n<small>BÊŸá´á´„á´‹á´‡á´…? UÉ´Ê™ÊŸá´á´„á´‹ á´›Êœá´‡ Ê™á´á´› á´›á´ Ê€á´‡á´„á´‡Éªá´ á´‡ á´á´‡êœ±êœ±á´€É¢ES.</small></i>",
                "search": True
            }
        }
        cfg = status_configs[key]
        user = await client.get_users(from_user)
        btn = [[InlineKeyboardButton(cfg["btn_text"], callback_data=f'{cfg["alert_key"]}#{from_user}')]]
        btn2 = [[
            InlineKeyboardButton('á´Šá´ÉªÉ´ á´„Êœá´€É´É´á´‡ÊŸ', url=UPDATE_CHNL_LNK, style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("á´ Éªá´‡á´¡ êœ±á´›á´€á´›á´œêœ±", url=f"{query.message.link}", style=enums.ButtonStyle.PRIMARY)
        ]]
        if cfg["search"]:
            btn2.append([InlineKeyboardButton("ðŸ” êœ±á´‡á´€Ê€á´„Êœ Êœá´‡Ê€á´‡ ðŸ”Ž", url=GRP_LNK, style=enums.ButtonStyle.SUCCESS)])
            
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
            "alalert": "Há´‡Ê {name}, Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Éªêœ± AÊŸÊ€á´‡á´€á´…Ê Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âœ…",
            "upalert": "Há´‡Ê {name}, Yá´á´œÊ€ Ê€á´‡Ç«á´œESêœ±á´› Éªêœ± Uá´˜ÊŸá´á´€á´…á´‡á´… ðŸ”¼",
            "unalert": "Há´‡Ê {name}, Yá´á´œÊ€ Ê€á´‡Ç«á´œá´‡êœ±á´› Éªêœ± UÉ´á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ âš ï¸",
            "hnalert": "Há´‡Ê {name}, TÊœÉªêœ± Éªêœ± Ná´á´› Aá´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ ÉªÉ´ HÉªÉ´á´…Éª âŒ",
            "nralert": "Há´‡Ê {name}, TÊœá´‡ Má´á´ Éªá´‡/êœ±Êœá´á´¡ Éªêœ± Ná´á´› Rá´‡ÊŸá´‡á´€êœ±á´‡á´… Yá´‡á´› ðŸ†•",
            "wsalert": "Há´‡Ê {name}, Yá´á´œÊ€ Rá´‡Ç«á´œá´‡êœ±á´› á´¡á´€êœ± Ê€á´‡á´Šá´‡á´„á´›á´‡á´… á´…á´œá´‡ á´›á´ á´¡Ê€á´É´É¢ sá´˜á´‡ÊŸÊŸÉªÉ´É¢ â—"
        }
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            msg_text = alerts[ident].format(name=user.first_name)
            await query.answer(msg_text, show_alert=True)
        else:
            await query.answer("Yá´á´œ á´…á´É´'á´› Êœá´€á´ á´‡ á´˜á´‡Ê€á´ÉªssÉªá´É´ á´›á´ sá´‡á´‡ á´›ÊœÉªêœ± âŒ", show_alert=True)

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
                            caption="âœ… <b>Here is your file directly!</b>\n\nâš ï¸ <i>Admin Note: BIN_CHANNEL/LOG_CHANNEL is not set with -100 ID in .env.</i>"
                        )
                        await query.answer("âœ… Sent file directly to your PM!\n(Stream requires valid channel setup)", show_alert=True)
                        return
                    except Exception as fallback_err:
                        logger.error("Direct send failed: %s", fallback_err)
                        await query.answer("âš ï¸ BIN_CHANNEL / LOG_CHANNEL is not configured!\nAdd bot as Admin with -100 ID in .env.", show_alert=True)
                        return

            user_id = query.from_user.id
            username = query.from_user.mention if query.from_user else f"User {user_id}"
            log_msg = None

            # 1. Attempt to send cached media to target_channel (with fallback to LOG_CHANNEL)
            try:
                log_msg = await client.send_cached_media(chat_id=target_channel, file_id=file_id)
            except Exception as channel_err:
                logger.warning("Failed sending to channel %s: %s", target_channel, channel_err)
                if target_channel != LOG_CHANNEL and LOG_CHANNEL and LOG_CHANNEL != -100:
                    logger.info("Attempting fallback to LOG_CHANNEL: %s", LOG_CHANNEL)
                    try:
                        log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
                        target_channel = LOG_CHANNEL
                    except Exception as log_err:
                        logger.error("Fallback to LOG_CHANNEL also failed: %s", log_err)

            # If sending to channel failed completely, send directly to user PM
            if not log_msg:
                try:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption="âœ… <b>Here is your file directly!</b>\n\nâš ï¸ <i>Stream setup failed: Ensure bot is Admin in your channel and channel ID starts with -100.</i>"
                    )
                    await query.answer("âœ… Sent file directly to your PM!\n\nFix Channel: Ensure ID starts with -100 & Bot is Admin.", show_alert=True)
                    return
                except Exception as dm_err:
                    logger.error("Direct PM send error: %s", dm_err)
                    await query.answer("âš ï¸ [400 CHAT_ID_INVALID]\nBot is not an Admin in channel!\n\n1. Channel ID must start with -100\n2. Add bot as Admin with 'Post Messages' rights.", show_alert=True)
                    return

            # 2. Extract safe filename and hash (never crashes if filename is None)
            raw_file_name = get_name(log_msg) or getattr(log_msg, 'caption', None) or 'file'
            file_name_clean = str(raw_file_name).strip() if raw_file_name else 'file'
            fileName = quote_plus(file_name_clean)
            file_hash = get_hash(log_msg) if hasattr(log_msg, 'id') else ''

            # 3. URL Validator: Telegram buttons strictly require valid http/https schemes with valid hosts (no localhost/0.0.0.0)
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

            # Clean UPDATE_CHNL_LNK
            clean_update = str(UPDATE_CHNL_LNK).strip() if UPDATE_CHNL_LNK else ""
            if clean_update.startswith("@"):
                clean_update = f"https://t.me/{clean_update[1:]}"
            elif clean_update and not clean_update.startswith("http"):
                clean_update = f"https://t.me/{clean_update}"
            if not clean_update or not _is_valid_url(clean_update):
                clean_update = "https://t.me/telegram"

            # 4. Post log notification to the channel (target_channel)
            log_btn = []
            if has_valid_url:
                log_btn = [[
                    InlineKeyboardButton("ðŸš€ êœ°á´€êœ±á´› á´…á´á´¡É´ÊŸá´á´€á´…", url=dreamx_download),
                    InlineKeyboardButton('ðŸ–¥ï¸ á´¡á´€á´›á´„Êœ á´É´ÊŸÉªÉ´á´‡', url=dreamx_stream)
                ]]

            log_text = (
                f"â€¢â€¢ ÊŸÉªÉ´á´‹ É¢á´‡É´á´‡Ê€á´€á´›á´‡á´… êœ°á´Ê€ Éªá´… #{user_id}\n"
                f"â€¢â€¢ á´œêœ±á´‡Ê€É´á´€á´á´‡ : {username}\n\n"
                f"â€¢â€¢ á–´áŽ¥á’ªá—´ Ná—©á—°á—´ : {file_name_clean}"
            )
            if not has_valid_url:
                log_text += "\n\nâš ï¸ <i>Note: Streaming URL pending (set FQDN in .env)</i>"

            # Send to channel (first try reply_to_message_id, then direct)
            try:
                await client.send_message(
                    chat_id=target_channel,
                    text=log_text,
                    reply_to_message_id=log_msg.id,
                    reply_markup=InlineKeyboardMarkup(log_btn) if log_btn else None
                )
            except Exception as reply_err:
                try:
                    await client.send_message(
                        chat_id=target_channel,
                        text=log_text,
                        reply_markup=InlineKeyboardMarkup(log_btn) if log_btn else None
                    )
                except Exception as send_err:
                    logger.warning("Could not send link log to channel: %s", send_err)

            # 5. Update user message buttons or provide fallback
            if has_valid_url:
                try:
                    await query.answer(MSG_ALRT)
                except Exception:
                    pass

                try:
                    dreamcinezone = await query.edit_message_reply_markup(
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("ðŸš€ êœ°á´€êœ±á´› á´…á´á´¡É´ÊŸá´á´€á´… ", url=dreamx_download, style=enums.ButtonStyle.PRIMARY),
                                InlineKeyboardButton('ðŸ–¥ï¸ á´¡á´€á´›á´„Êœ á´É´ÊŸÉªÉ´á´‡ ðŸ–¥ï¸', url=dreamx_stream, style=enums.ButtonStyle.SUCCESS)
                            ],
                            [
                                InlineKeyboardButton('ðŸŒ¹ ð‰á´ÉªÉ´ ð”á´©á´…á´€á´›á´‡êœ± ð‚Êœá´€É´É´á´‡ÊŸ ðŸŒ¹', url=clean_update, style=enums.ButtonStyle.DANGER)
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
                    logger.error("Failed to edit reply markup with stream URLs: %s", edit_err)

            # If no valid streaming URL (e.g. FQDN not configured in .env):
            # Send file directly to user PM so user is never left without the movie!
            try:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=(
                        f"âœ… <b>{file_name_clean}</b>\n\n"
                        f"âš ï¸ <b>Web Streaming Pending Configuration</b>\n"
                        f"<i>Web Stream & Fast Download buttons require a public bot domain. Set <code>FQDN=your-bot.onrender.com</code> in your .env file!</i>"
                    )
                )
            except Exception as direct_err:
                logger.warning("Direct send to user PM failed: %s", direct_err)

            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton('ðŸŒ¹ ð‰á´ÉªÉ´ ð”á´©á´…á´€á´›á´‡êœ± ð‚Êœá´€É´É´á´‡ÊŸ ðŸŒ¹', url=clean_update, style=enums.ButtonStyle.DANGER)
                        ]
                    ])
                )
            except Exception:
                pass

            await query.answer(
                "âš ï¸ FQDN is not configured in .env!\n\n"
                "1. Add FQDN=your-bot.onrender.com in your bot's environment variables (Render/VPS).\n"
                "2. File has been sent directly to your PM!",
                show_alert=True
            )
            return

        except Exception as e:
            logger.error("Callback error in generate_stream_link: %s", e)
            err_msg = str(e)
            if "CHAT_ID_INVALID" in err_msg:
                try:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption="âœ… <b>Here is your file directly!</b>\n\nâš ï¸ <i>Fix BIN_CHANNEL: Add bot as Admin in your channel and ensure ID starts with -100!</i>"
                    )
                    await query.answer("âœ… Sent file directly to your PM!\n(Fix BIN_CHANNEL: Add bot as Admin with -100)", show_alert=True)
                    return
                except Exception:
                    pass
                await query.answer("âš ï¸ Telegram: [400 CHAT_ID_INVALID]\nBot is not an Admin in channel!\n\n1. Channel ID must start with -100\n2. Add bot as Admin in that channel.", show_alert=True)
            elif "BUTTON_URL_INVALID" in err_msg:
                try:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption="âœ… <b>Here is your file directly!</b>\n\nâš ï¸ <i>BUTTON_URL_INVALID: Set FQDN=your-bot.onrender.com in .env so Telegram can build valid stream links!</i>"
                    )
                    await query.answer("âš ï¸ Telegram: [400 BUTTON_URL_INVALID]\nSet FQDN in your .env!\nFile sent directly to your PM.", show_alert=True)
                    return
                except Exception:
                    pass
                await query.answer("âš ï¸ [400 BUTTON_URL_INVALID]\nSet FQDN=your-bot.onrender.com in .env", show_alert=True)
            else:
                await query.answer(f"âš ï¸ Stream link issue:\n{e}", show_alert=True)
            return


    elif query.data == "prestream":
        await query.answer(text=script.PRE_STREAM_ALERT, show_alert=True)
        dreamcinezone = await client.send_photo(
            chat_id=query.message.chat.id,
            photo="https://i.ibb.co/whf8xF7j/photo-2025-07-26-10-42-46-7531339305176793100.jpg",
            caption=script.PRE_STREAM,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ðŸš€ ðð”ð˜ ðð‘ð„ðŒðˆð”ðŒ ðŸš€", callback_data="premium_info", style=enums.ButtonStyle.DANGER)]
            ])
        )
        await asyncio.sleep(DELETE_TIME)
        await dreamcinezone.delete()




    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('âœ§ á´€á´…á´… á´á´‡ á´›á´ Êá´á´œÊ€ É¢Ê€á´á´œá´˜ âœ§', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true', style=enums.ButtonStyle.SUCCESS)
                ],[
                    InlineKeyboardButton('ð–£ â€Œ Êœá´‡ÊŸá´˜ ð–£ â€Œ ', callback_data="help", style=enums.ButtonStyle.PRIMARY),
                     InlineKeyboardButton('áª¥ á´€Ê™á´á´œá´› áª¥', callback_data="about", style=enums.ButtonStyle.PRIMARY),
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour
        if curr_time < 12:
            gtxt = "É¢á´á´á´… á´á´Ê€É´ÉªÉ´É¢ ðŸŒž"
        elif curr_time < 17:
            gtxt = "É¢á´á´á´… á´€Ò“á´›á´‡Ê€É´á´á´É´ ðŸŒ“"
        elif curr_time < 21:
            gtxt = "É¢á´á´á´… á´‡á´ á´‡É´ÉªÉ´É¢ ðŸŒ˜"
        else:
            gtxt = "É¢á´á´á´… É´ÉªÉ¢Êœá´› ðŸŒ‘"
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
                InlineKeyboardButton('ðŸŒ² Sá´‡É´á´… Dá´É´á´€á´›á´‡ Sá´„Ê€á´‡á´‡É´sÊœá´á´› Há´‡Ê€á´‡', url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)
            ],[
                InlineKeyboardButton('â‡ Ê™á´€á´„á´‹ â‡', callback_data='about', style=enums.ButtonStyle.DANGER)
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(text="â— â—Œ â—Œ")
        await query.message.edit_text(text="â— â— â—Œ")
        await query.message.edit_text(text="â— â— â—")
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
            InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ á´›á´ Êœá´á´á´‡ â‡‹', callback_data='start', style=enums.ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('âƒ É¢Ê€á´á´œá´˜ âƒ', url='https://t.me/movies_4uz', style=enums.ButtonStyle.SUCCESS),
            InlineKeyboardButton (' â«¹â«º á´„Êœá´€É´É´á´‡ÊŸ â«¹â«º ', url='https://t.me/movies4u_backup', style=enums.ButtonStyle.SUCCESS),
        ],[
            InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ á´›á´ Êœá´á´á´‡ â‡‹', callback_data='start', style=enums.ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer(
                    "ðŸš¸ Êá´á´œ'á´ á´‡ á´€ÊŸÊ€á´‡á´€á´…Ê á´„ÊŸá´€Éªá´á´‡á´… Êá´á´œÊ€ êœ°Ê€á´‡á´‡ á´›Ê€Éªá´€ÊŸ á´É´á´„á´‡ !\n\nðŸ“Œ á´„Êœá´‡á´„á´‹á´á´œá´› á´á´œÊ€ á´˜ÊŸá´€É´êœ± Ê™Ê : /plan",
                    show_alert=True
                )
                return
            else:
                await db.give_free_trial(user_id)
                await query.answer("âœ… Trial activated!", show_alert=True)

                msg = await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo="https://i.ibb.co/0jC8MSDZ/photo-2025-07-26-10-42-36-7531339283701956616.jpg",
                    caption=(
                        "<b>ðŸ¥³ á´„á´É´É¢Ê€á´€á´›á´œÊŸá´€á´›Éªá´É´êœ±\n\n"
                        "ðŸŽ‰ Êá´á´œ á´„á´€É´ á´œsá´‡ êœ°Ê€á´‡á´‡ á´›Ê€á´€ÉªÊŸ êœ°á´Ê€ <u>5 á´ÉªÉ´á´œá´›á´‡s</u> êœ°Ê€á´á´ É´á´á´¡ !\n\n"
                        "É´á´‡á´‡á´… á´˜Ê€á´‡á´Éªá´œá´ ðŸ‘‰ðŸ» /plan</b>"
                    ),
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("ðŸš€ ðð”ð˜ ðð‘ð„ðŒðˆð”ðŒ ðŸš€", callback_data="premium_info", style=enums.ButtonStyle.PRIMARY)
                    ]])
                )
                await asyncio.sleep(DELETE_TIME)
                return await msg.delete()
        except Exception:
            logging.exception("Error in give_trial callback")



    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('á´©Ê€á´á´ Éªá´…á´‡Ê€Ê™á´á´›á´¢', url='https://tx.me/ProviderBotz', style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ â‡‹', callback_data='about', style=enums.ButtonStyle.DANGER)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)

    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("â‡‹ Ê™á´€á´„á´‹ â‡‹", callback_data="about", style=enums.ButtonStyle.PRIMARY)
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    elif query.data == "premium_info":
        try:
            btn = [[
                InlineKeyboardButton('â€¢ Ê™á´œÊ á´˜Ê€á´‡á´Éªá´œá´ â€¢', callback_data='buy_info', style=enums.ButtonStyle.PRIMARY),
            ],[
                InlineKeyboardButton('â€¢ Ê€á´‡êœ°á´‡Ê€ êœ°Ê€Éªá´‡É´á´…êœ±', callback_data='reffff', style=enums.ButtonStyle.SUCCESS),
                InlineKeyboardButton('êœ°Ê€á´‡á´‡ á´›Ê€Éªá´€ÊŸ â€¢', callback_data='give_trial', style=enums.ButtonStyle.PRIMARY)
            ],[
                InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ á´›á´ Êœá´á´á´‡ â‡‹', callback_data='start', style=enums.ButtonStyle.DANGER)
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.BPREMIUM_TXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=reply_markup
            )
        except Exception:
            logging.exception("Exception in 'premium_info' callback")


    elif query.data == "buy_info":
        try:
            btn = [[
                InlineKeyboardButton('êœ±á´›á´€Ê€', callback_data='star_info', style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton('á´œá´˜Éª', callback_data='upi_info', style=enums.ButtonStyle.PRIMARY)
            ],[
                InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ á´›á´ á´˜Ê€á´‡á´Éªá´œá´ â‡‹', callback_data='premium_info', style=enums.ButtonStyle.DANGER)
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_TEXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=reply_markup
            )
        except Exception:
            logging.exception("Exception in 'buy_info' callback")

    elif query.data == "upi_info":
        try:
            btn = [[
                InlineKeyboardButton('â€¢ êœ±á´‡É´á´…  á´˜á´€Êá´á´‡É´á´› êœ±á´„Ê€á´‡á´‡É´êœ±Êœá´á´› â€¢', url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY),
            ],[
                InlineKeyboardButton('â‡‹ Ê™á´€á´„á´‹ â‡‹', callback_data='buy_info', style=enums.ButtonStyle.DANGER)
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_UPI_TEXT.format(OWNER_UPI_ID), parse_mode=enums.ParseMode.HTML),
                reply_markup=reply_markup
            )
        except Exception:
            logging.exception("Exception in 'upi_info' callback")

    elif query.data == "star_info":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}â­", callback_data=f"buy_{stars}", style=enums.ButtonStyle.PRIMARY)
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("â‹ž Ê™á´€á´„á´‹", callback_data="buy_info", style=enums.ButtonStyle.DANGER)])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                media=InputMediaPhoto(media=SUBSCRIPTION, caption=script.PREMIUM_STAR_TEXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=reply_markup
            )
        except Exception:
            logging.exception("Exception in 'star' callback")


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
        data = query.data
        grp_id = int(data.split("#")[1])
        if not await is_check_admin(client, grp_id, query.from_user.id):
            return await query.answer(script.NT_ADMIN_ALRT_TXT, show_alert=True)
        await db.remove_group_connection(grp_id, user_id)
        await query.answer("Group removed from your connections.", show_alert=True)
        connected_groups = await db.get_connected_grps(user_id)
        if not connected_groups:
            await query.edit_message_text("Ná´ Cá´É´É´á´‡á´„á´›á´‡á´… GÊ€á´á´œá´˜s Fá´á´œÉ´á´… .")
            return
        group_list = []
        for group in connected_groups:
            try:
                Chat = await client.get_chat(group)
                group_list.append([
                    InlineKeyboardButton(
                        text=Chat.title, callback_data=f"grp_pm#{Chat.id}")
                ])
            except Exception:
                pass
        await query.edit_message_text(
            "âš ï¸ êœ±á´‡ÊŸá´‡á´„á´› á´›Êœá´‡ É¢Ê€á´á´œá´˜ á´¡Êœá´êœ±á´‡ êœ±á´‡á´›á´›ÉªÉ´É¢êœ± Êá´á´œ á´¡á´€É´á´› á´›á´ á´„Êœá´€É´É¢á´‡.\n\n"
            "Éªêœ° Êá´á´œÊ€ É¢Ê€á´á´œá´˜ Éªêœ± É´á´á´› êœ±Êœá´á´¡ÉªÉ´É¢ Êœá´‡Ê€á´‡,\n"
            "á´œêœ±á´‡ /reload ÉªÉ´ á´›Êœá´€á´› É¢Ê€á´á´œá´˜ á´€É´á´… Éªá´› á´¡ÉªÊŸÊŸ á´€á´˜á´˜á´‡á´€Ê€ Êœá´‡Ê€á´‡.",
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
            await query.answer("á´êœ°êœ° âœ—")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("á´É´ âœ“")
        settings = await get_settings(int(grp_id))
        if settings is not None:
            btn = await group_setting_buttons(int(grp_id))
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    """
    Core auto_filter logic with timing/debug logging removed.
    """
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
            # ignore scheduling errors
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
                removes = ["in", "upload", "series", "full",
                           "horror", "thriller", "mystery", "print", "file"]
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
                        ai_sts = await m.edit('ðŸ¤– á´˜ÊŸá´‡á´€êœ±á´‡ á´¡á´€Éªá´›, á´€Éª Éªêœ± á´„Êœá´‡á´„á´‹ÉªÉ´É¢ Êá´á´œÊ€ êœ±á´˜á´‡ÊŸÊŸÉªÉ´É¢...')
                        is_misspelled = await ai_spell_check(chat_id=message.chat.id, wrong_name=search)
                        if is_misspelled:
                            await ai_sts.edit(f'âœ… AÉª Sá´œÉ¢É¢á´‡sá´›á´‡á´…: <code>{is_misspelled}</code>\nðŸ” Searching for it...')
                            message.text = is_misspelled
                            await ai_sts.delete()
                            return await auto_filter(client, message)
                        await ai_sts.delete()
                        result = await advantage_spell_chok(client, message)
                        return result
                    else:
                        try:
                            if m:
                                await m.delete()
                        except Exception:
                            pass
                        result = await advantage_spell_chok(client, message)
                        return result
            else:
                return
        else:
            message = msg.message.reply_to_message
            search, files, offset, total_results = spoll
            m = await message.reply_text(f'ðŸ”Ž sá´‡á´€Ê€á´„ÊœÉªÉ´É¢ {search}')
            settings = await get_settings(message.chat.id)
            await msg.message.delete()
        key = f"{message.chat.id}-{message.id}"
        FRESH[key] = search
        temp.GETALL[key] = files
        req = message.from_user.id if message.from_user else 0
        temp.SHORT[message.from_user.id] = message.chat.id
        try:
            await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji="ðŸ¿")
        except Exception:
            pass
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(text=f"{get_size(file.file_size)} â‰½ " + clean_filename(
                        file.file_name), callback_data=f'file#{file.file_id}'),
                ]
                for file in files
            ]
            btn.insert(0,
                       [
                           InlineKeyboardButton(
                               'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                           InlineKeyboardButton(
                               "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                           InlineKeyboardButton(
                               "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                       ]
                       )
            [
    InlineKeyboardButton(
        "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
            ]
        else:
            btn = []
            btn.insert(0,
                       [
                           InlineKeyboardButton(
                               'ðá´œá´€ÊŸÉªá´›Ê', callback_data=f"qualities#{req}#{key}", style=enums.ButtonStyle.DANGER),
                           InlineKeyboardButton(
                               "ð‹á´€É´É¢á´œá´€É¢á´‡", callback_data=f"languages#{req}#{key}", style=enums.ButtonStyle.PRIMARY),
                           InlineKeyboardButton(
                               "ð’á´‡á´€sá´É´",  callback_data=f"seasons#{req}#{key}", style=enums.ButtonStyle.DANGER)
                       ]
                       )
            [
    InlineKeyboardButton(
        "ðŸ—ƒï¸ Sá´‡É´á´… AÊŸÊŸ ðŸ—ƒï¸",
        callback_data=...,
        style=enums.ButtonStyle.SUCCESS
    )
            ]

        if offset != "":
            req = message.from_user.id if message.from_user else 0
            if ULTRA_FAST_MODE:
                btn.append(
                    [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                        text="1", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                )
            else:
                try:
                    if settings['max_btn']:
                        btn.append(
                            [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                                text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                        )
                    else:
                        btn.append(
                            [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                                text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                        )
                except KeyError:
                    await save_group_settings(message.chat.id, 'max_btn', True)
                    btn.append(
                        [InlineKeyboardButton("á´˜á´€É¢á´‡", callback_data="pages", style=enums.ButtonStyle.DANGER), InlineKeyboardButton(
                            text=f"1/{math.ceil(int(total_results)/10)}", callback_data="pages", style=enums.ButtonStyle.SUCCESS), InlineKeyboardButton(text="É´á´‡xá´› â‹Ÿ", callback_data=f"next_{req}_{key}_{offset}", style=enums.ButtonStyle.DANGER)]
                    )
        else:
            btn.append([InlineKeyboardButton(
                text="â†­ É´á´ á´á´Ê€á´‡ á´˜á´€É¢á´‡êœ± á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ â†­", callback_data="pages")])

        if settings.get('imdb'):
            imdb = await get_posterx(search, file=(files[0]).file_name) if TMDB_POSTER else await get_poster(search, file=(files[0]).file_name)
        else:
            imdb = None
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - \
            timedelta(hours=curr_time.hour, minutes=curr_time.minute,
                      seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        TEMPLATE = script.IMDB_TEMPLATE_TXT
        settings = await get_settings(message.chat.id)
        if settings.get('template'):
            TEMPLATE = settings['template']
        if imdb:
            cap = TEMPLATE.format(
                query=search,
                title=imdb['title'],
                votes=imdb['votes'],
                aka=imdb["aka"],
                seasons=imdb["seasons"],
                box_office=imdb['box_office'],
                localized_title=imdb['localized_title'],
                kind=imdb['kind'],
                imdb_id=imdb["imdb_id"],
                cast=imdb['cast'],
                runtime=imdb['runtime'],
                countries=imdb['countries'],
                certificates=imdb['certificates'],
                languages=imdb['languages'],
                director=imdb['director'],
                writer=imdb['writer'],
                producer=imdb['producer'],
                composer=imdb['composer'],
                cinematographer=imdb['cinematographer'],
                music_team=imdb['music_team'],
                distributors=imdb['distributors'],
                release_date=imdb['release_date'],
                year=imdb['year'],
                genres=imdb['genres'],
                poster=imdb['poster'],
                plot=imdb['plot'] if settings.get('button') else "N/A",
                rating=imdb['rating'],
                url=imdb['url'],
                **locals()
            )
            temp.IMDB_CAP[message.from_user.id] = cap
            if not settings.get('button'):
                cap += "\n\n<b><u>Your Requested Files Are Here</u></b>\n\n"
                for idx, file in enumerate(files, start=1):
                    cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
        else:
            temp.IMDB_CAP[message.from_user.id] = None
            if ULTRA_FAST_MODE:
                if settings.get('button'):
                    cap = f"<b>ðŸ· á´›Éªá´›ÊŸá´‡ : <code>{search}</code>\nâ° Ê€á´‡sá´œÊŸá´› ÉªÉ´ : <code>{remaining_seconds} Sá´‡á´„á´É´á´…s</code>\n\nðŸ“ Ê€á´‡Ç«á´œá´‡sá´›á´‡á´… Ê™Ê : {message.from_user.mention}\nâšœï¸ á´˜á´á´¡á´‡Ê€á´‡á´… Ê™Ê : âš¡ {message.chat.title or temp.B_LINK or 'á´…Ê€á´‡á´€á´xÊ™á´á´›á´¢'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"
                else:
                    cap = f"<b>ðŸ· á´›Éªá´›ÊŸá´‡ : <code>{search}</code>\nâ° Ê€á´‡sá´œÊŸá´› ÉªÉ´ : <code>{remaining_seconds} Sá´‡á´„á´É´á´…s</code>\n\nðŸ“ Ê€á´‡Ç«á´œá´‡sá´›á´‡á´… Ê™Ê : {message.from_user.mention}\nâšœï¸ á´˜á´á´¡á´‡Ê€á´‡á´… Ê™Ê : âš¡ {message.chat.title or temp.B_LINK or 'á´…Ê€á´‡á´€á´xÊ™á´á´›á´¢'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"
                    for idx, file in enumerate(files, start=1):
                        cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
            else:
                if settings.get('button'):
                    cap = f"<b>ðŸ· á´›Éªá´›ÊŸá´‡ : <code>{search}</code>\nðŸ§± á´›á´á´›á´€ÊŸ êœ°ÉªÊŸá´‡êœ± : <code>{total_results}</code>\nâ° Ê€á´‡sá´œÊŸá´› ÉªÉ´ : <code>{remaining_seconds} Sá´‡á´„á´É´á´…s</code>\n\nðŸ“ Ê€á´‡Ç«á´œá´‡sá´›á´‡á´… Ê™Ê : {message.from_user.mention}\nâšœï¸ á´˜á´á´¡á´‡Ê€á´‡á´… Ê™Ê : âš¡ {message.chat.title or temp.B_LINK or 'á´…Ê€á´‡á´€á´xÊ™á´á´›á´¢'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"
                else:
                    cap = f"<b>ðŸ· á´›Éªá´›ÊŸá´‡ : <code>{search}</code>\nðŸ§± á´›á´á´›á´€ÊŸ êœ°ÉªÊŸá´‡êœ± : <code>{total_results}</code>\nâ° Ê€á´‡sá´œÊŸá´› ÉªÉ´ : <code>{remaining_seconds} Sá´‡á´„á´É´á´…s</code>\n\nðŸ“ Ê€á´‡Ç«á´œá´‡sá´›á´‡á´… Ê™Ê : {message.from_user.mention}\nâšœï¸ á´˜á´á´¡á´‡Ê€á´‡á´… Ê™Ê : âš¡ {message.chat.title or temp.B_LINK or 'á´…Ê€á´‡á´€á´xÊ™á´á´›á´¢'} \n\n<u>Your Requested Files Are Here</u> \n\n</b>"

                    for idx, file in enumerate(files, start=1):
                        cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
        sent = None
        try:
            if imdb and imdb.get('poster'):
                try:
                    if TMDB_POSTER:
                        photo = imdb.get('backdrop') if imdb.get('backdrop') and LANDSCAPE_POSTER else imdb.get('poster')
                    else:
                        photo = imdb.get('poster')
                    sent = await message.reply_photo(photo=photo, caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    if m:
                        await m.delete()
                except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                    pic = imdb.get('poster')
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    sent = await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    if m:
                        await m.delete()
                except Exception as e:
                    logger.exception(e)
                    sent = await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            else:
                sent = await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
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
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        if not search_results or not hasattr(search_results, "titles"):
            return []
        movie_list = [movie.title for movie in search_results.titles]
        return movie_list
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
        google = quote_plus(search)
        button = [[InlineKeyboardButton(
            "Ê€á´‡Ç«á´œá´‡sá´› ðŸ“ á´€á´…á´ÉªÉ´", url=OWNER_LNK, style=enums.ButtonStyle.PRIMARY)]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except Exception:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [
        [InlineKeyboardButton(text=movie.title, callback_data=f"spol#{movie.imdb_id}#{user}")
         ] for movie in movies]

    buttons.append([InlineKeyboardButton(
        text="ðŸš« á´„ÊŸá´sá´‡ ðŸš«", callback_data='close_data', style=enums.ButtonStyle.DANGER)])
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons))
    await asyncio.sleep(60)
    await d.delete()
    try:
        await message.delete()
    except Exception:
        pass
    
