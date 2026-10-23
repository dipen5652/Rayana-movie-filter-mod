import logging
import re
import os
import random
import string
from info import ULTRA_FAST_MODE, MAX_LIST_ELM, BAD_WORDS, LONG_IMDB_DESCRIPTION, IS_VERIFY, MAX_B_TN, TUTORIAL, TUTORIAL_2, TUTORIAL_3, LOG_CHANNEL, TMDB_ON_SEARCH
from imdbkit import IMDBKit # pyrefly: ignore 
import asyncio
from pyrogram.types import Message, InlineKeyboardButton
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid, ChatAdminRequired
from pyrogram import enums
from typing import Union
from Script import script
from typing import List
from database.users_chats_db import db
from bs4 import BeautifulSoup
import aiohttp
from shortzy import Shortzy
from plugins.Dreamxfutures.Imdbposter import get_movie_detailsx


logger = logging.getLogger(__name__)

def get_random_mix_id():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=6))

BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\((buttonurl\vert{}buttonalert):(?:/{0,2})(.+?)(:same)?\))"
)

imdb = IMDBKit()

BANNED = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)


class temp(object):   
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT = int(os.environ.get("SKIP", 2))
    CANCEL = False
    B_USERS_CANCEL = False
    B_GROUPS_CANCEL = False 
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    B_LINK = None
    SETTINGS = {}
    GETALL = {}
    SHORT = {}
    IMDB_CAP = {}
    VERIFICATIONS = {}
    TEMP_INVITE_LINKS = {}
    REQ_LINKS = {}


async def is_req_subscribed(bot, user_id, rqfsub_channels):
    btn = []

    async def check_req_channel(ch_id):
        if await db.has_joined_channel(user_id, ch_id):
            return None
        try:
            member = await bot.get_chat_member(ch_id, user_id)
            if member.status != enums.ChatMemberStatus.BANNED:
                await db.add_join_req(user_id, ch_id)
                return None
        except UserNotParticipant:
            pass
        except Exception as e:
            logger.error(f"Error checking membership in {ch_id}: {e}")

        try:
            chat = await bot.get_chat(ch_id)
            if ch_id in temp.REQ_LINKS:
                invite_link = temp.REQ_LINKS[ch_id]
            else:
                invite = await bot.create_chat_invite_link(
                    ch_id,
                    creates_join_request=True
                )
                invite_link = invite.invite_link
                temp.REQ_LINKS[ch_id] = invite_link

            return [InlineKeyboardButton(f"⛔️ Join {chat.title}", url=invite_link, style=enums.ButtonStyle.PRIMARY)]
        except ChatAdminRequired:
            logger.warning(f"Bot not admin in {ch_id}")
        except Exception as e:
            logger.warning(f"Invite link error for {ch_id}: {e}")
        return None

    tasks = [check_req_channel(ch_id) for ch_id in rqfsub_channels]
    results = await asyncio.gather(*tasks)

    for res in results:
        if res:
            btn.append(res)

    return btn

async def is_subscribed(bot, user_id, fsub_channels):
    btn = []
    
    async def check_channel(channel_id):
        try:
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            try:
                chat = await bot.get_chat(int(channel_id))
                invite_link = await bot.create_chat_invite_link(channel_id)
                return InlineKeyboardButton(f"📢 Join {chat.title}", url=invite_link.invite_link)
            except Exception as e:
                logger.warning(f"Failed to create invite for {channel_id}: {e}")
        except Exception as e:
            logger.exception(f"is_subscribed error for {channel_id}: {e}")
        return None

    tasks = [check_channel(channel_id) for channel_id in fsub_channels]
    results = await asyncio.gather(*tasks)

    for button in results:
        if button:
            btn.append([button])
            
    return btn

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except Exception:
        return False
    
async def users_broadcast(user_id, message, is_pin):
    try:
        m = await message.copy(chat_id=user_id)
        if is_pin:
            await m.pin(both_sides=True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await users_broadcast(user_id, message, is_pin)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logger.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        logger.error(f"[BROADCAST FAIL] user={user_id} | {type(e).__name__}: {e}")
        return False, "Error"


async def groups_broadcast(chat_id, message, is_pin):
    try:
        m = await message.copy(chat_id=chat_id)
        if is_pin:
            try:
                await m.pin()
            except Exception:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await groups_broadcast(chat_id, message, is_pin)
    except Exception:
        await db.delete_chat(chat_id)
        return "Error"

async def junk_group(chat_id, message):
    try:
        kk = await message.copy(chat_id=chat_id)
        await kk.delete(True)
        return True, "Succes", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await junk_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))       
        logger.info(f"{chat_id} - PeerIdInvalid")
        return False, "deleted", f'{e}\n\n'
    

async def clear_junk(user_id, message):
    try:
        key = await message.copy(chat_id=user_id)
        await key.delete(True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await clear_junk(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logger.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception:
        return False, "Error"
     
async def get_status(bot_id):
    try:
        return await db.movie_update_status(bot_id) or False  
    except Exception as e:
        logger.error(f"Error in get_movie_update_status: {e}")
        return False  

async def add_name_to_db(filename):
    """
    Helper function to add a filename to the database.
    """
    return await db.add_name(filename) 


def listx_to_str(k):
    if k is None or k == "":
        return "N/A"
    
    if not hasattr(k, '__iter__') or isinstance(k, (str, int, float)):
        return str(k)
    
    result = []
    for elem in k:
        if elem and str(elem).strip():
            result.append(str(elem).strip())
    
    if MAX_LIST_ELM and len(result) > MAX_LIST_ELM:
        result = result[:int(MAX_LIST_ELM)]
    
    return ', '.join(result) if result else "N/A"
    
async def get_poster(query, bulk=False, id=False, file=None):
    async def _fetch_imdb_data():
        if not id:
            clean_query = (query.strip()).lower()
            title = clean_query
            year_val = None
            
            year_list = re.findall(r'[1-2]\d{3}$', clean_query, re.IGNORECASE)
            if year_list:
                year_val = year_list[0]
                title = (clean_query.replace(year_val, "")).strip()
            elif file is not None:
                year_list = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                if year_list:
                    year_val = year_list[0]
            
            search_result = await asyncio.to_thread(imdb.search_movie, title.lower())
            if not search_result or not search_result.titles:
                return None
            
            movie_list = search_result.titles[:MAX_LIST_ELM]
            
            if year_val:
                filtered = [m for m in movie_list if m.year and str(m.year) == str(year_val)]
                if not filtered:
                    filtered = movie_list
            else:
                filtered = movie_list
                
            kind_filter = ['movie', 'tv series', 'tvSeries', 'tvMiniSeries', 'tvMovie']
            filtered_kind = [m for m in filtered if m.kind and m.kind in kind_filter]
            
            if not filtered_kind:
                filtered_kind = filtered
            
            if bulk:
                return filtered_kind[:MAX_LIST_ELM]
            if not filtered_kind:
                return None   
            movie_brief = filtered_kind[0]
            movieid_str = movie_brief.imdb_id 
        else:
            movieid_str = query

        movie = await asyncio.to_thread(imdb.get_movie, movieid_str)
        if not movie:
            return None

        if movie.release_date:
            date = movie.release_date
        elif movie.year:
            date = str(movie.year)
        else:
            date = "N/A"
            
        plot = movie.plot[0] if isinstance(movie.plot, list) else movie.plot or ""
        if len(plot) > 800:
            plot = plot[:800] + "..."
        imdb_id = movie.imdb_id
        if not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"
        return {
            'title': movie.title,
            'votes': movie.votes,
            "aka": listx_to_str(movie.title_akas),
            "seasons": (
                len(movie.info_series.display_seasons)
                if getattr(movie, "info_series", None)
                and getattr(movie.info_series, "display_seasons", None)
                else "N/A"
            ),
            "box_office": movie.worldwide_gross,
            'localized_title': movie.title_localized,
            'kind': movie.kind,
            "imdb_id": imdb_id,
            "cast": listx_to_str(movie.stars),
            "runtime": listx_to_str(movie.duration),
            "countries": listx_to_str(movie.countries),
            "certificates": listx_to_str(movie.certificates),
            "languages": listx_to_str(movie.languages),
            "director": listx_to_str(movie.directors),
            "writer": listx_to_str([p.name for p in movie.writers]),
            "producer": listx_to_str([p.name for p in movie.producers]),
            "composer": listx_to_str([p.name for p in movie.composers]),
            "cinematographer": listx_to_str([p.name for p in movie.cinematographers]),
            "music_team": listx_to_str([p.name for p in movie.music_team]),
            "distributors": listx_to_str([c.name for c in movie.distributors]),        
            'release_date': date,
            'year': movie.year,
            'genres': listx_to_str(movie.genres),
            'poster': movie.cover_url,
            'plot': plot,
            'rating': str(movie.rating),
            "url": movie.url or f"https://www.imdb.com/title/{imdb_id}"
        }

    try:
        return await asyncio.wait_for(_fetch_imdb_data(), timeout=4.5)
    except asyncio.TimeoutError:
        logger.warning(f"IMDb request timed out for '{query}', continuing without IMDb metadata.")
        return None
    except Exception as e:
        logger.error(f"Error in get_poster: {e}")
        return None
    
# Backward-compatibility fallback (Safe alias to get_poster)
async def old_get_poster(query, bulk=False, id=False, file=None):
    return await get_poster(query, bulk=bulk, id=id, file=file)
    
async def get_posterx(query, bulk=False, id=False, file=None):
    """
    Fetches movie details from TMDB using the get_movie_detailsx helper
    and formats the output to be compatible with the original get_poster function.
    """
    if not id:
        details = await get_movie_detailsx(query, file=file)
    else:
        details = await get_movie_detailsx(query, id=True)

    if not details or details.get("error"):
        return None
    
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = details.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = details.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

    def list_to_str_internal(val):
        if isinstance(val, list):
            return ", ".join(str(x) for x in val if x)
        return str(val) if val else ""

    return {
        'title': details.get('title'),
        'votes': details.get('votes'),
        "aka": None,
        "seasons": details.get('seasons'),
        "box_office": details.get('box_office'),
        'localized_title': details.get('localized_title'),
        'kind': 'movie' if 'movie' in details.get('tmdb_url', '') else 'tv series',
        "imdb_id": details.get('imdb_id'),
        "cast": list_to_str_internal(details.get("cast")),
        "runtime": list_to_str_internal(details.get("runtime")),
        "countries": list_to_str_internal(details.get("countries")),
        "certificates": list_to_str_internal(details.get("certificates")),
        "languages": list_to_str_internal(details.get("languages")),
        "director": list_to_str_internal(details.get("director")),
        "writer": list_to_str_internal(details.get("writer")),
        "producer": list_to_str_internal(details.get("producer")),
        "composer": list_to_str_internal(details.get("composer")),
        "cinematographer": list_to_str_internal(details.get("cinematographer")),
        "music_team": None,
        "distributors": list_to_str_internal(details.get("distributors")),
        'release_date': details.get('release_date'),
        'year': details.get('year'),
        'genres': list_to_str_internal(details.get("genres")),
        'poster': details.get('poster_url'),
        'backdrop': details.get('backdrop_url'),
        'plot': plot,
        'rating': str(details.get("rating", "N/A")),
        'url': details.get('tmdb_url')
    }
    
async def search_gagala(text):
    usr_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/61.0.3163.100 Safari/537.36'
    }
    text = text.replace(" ", "+")
    url = f"https://www.google.com/search?q={text}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=usr_agent, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                html = await response.text()

        soup = await asyncio.to_thread(BeautifulSoup, html, 'html.parser')
        titles = soup.find_all('h3')
        return [title.get_text() for title in titles if title.get_text().strip()]
    except Exception as e:
        logger.warning(f"search_gagala error: {e}")
        return []

async def get_shortlink(link, grp_id, is_second_shortener=False, is_third_shortener=False):
    settings = await get_settings(grp_id)
    if is_third_shortener:             
        api, site = settings['api_three'], settings['shortner_three']
    else:
        if is_second_shortener:
            api, site = settings['api_two'], settings['shortner_two']
        else:
            api, site = settings['api'], settings['shortner']
    shortzy = Shortzy(api, site)
    try:
        link = await shortzy.convert(link)
    except Exception:
        link = await shortzy.get_quick_link(link)
    return link

async def get_settings(group_id):
    group_id = int(group_id)
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS[group_id] = settings.copy()
    return settings
    
async def save_group_settings(group_id, key, value):
    group_id = int(group_id)
    current = await get_settings(group_id)
    current = current.copy()
    current.update({key: value})
    temp.SETTINGS[group_id] = current
    await db.update_settings(group_id, current)

async def delete_group_setting(group_id, key):
    group_id = int(group_id)
    current = await get_settings(group_id)
    current = current.copy()
    if key in current:
        current.pop(key)
        temp.SETTINGS[group_id] = current
        await db.update_settings(group_id, current)

def clean_filename(file_name):
    prefixes = ('[', '@', 'www.')
    unwanted = {word.lower() for word in BAD_WORDS}
    
    file_name = ' '.join(
        word for word in file_name.split()
        if not (word.startswith(prefixes) or word.lower() in unwanted)
    )
    return file_name

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]  

def extract_request_content(message_text):
    match = re.search(r"<u>(.*?)</u>", message_text)
    if match:
        return match.group(1).strip()
    match = re.search(r"📝 ʀᴇǫᴜᴇꜱᴛ ?: ?(.*?)(?:\n|$)", message_text)
    if match:
        return match.group(1).strip()
    return message_text.strip()

def generate_settings_text(settings, title, reset_done=False):
    note = "\n<b>📌 ɴᴏᴛᴇ :- ʀᴇꜱᴇᴛ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ✅</b>" if reset_done else ""
    s_short = settings.get("shortner", "N/A")
    s_api = settings.get("api", "N/A")
    s_short2 = settings.get("shortner_two", "N/A")
    s_api2 = settings.get("api_two", "N/A")
    s_short3 = settings.get("shortner_three", "N/A")
    s_api3 = settings.get("api_three", "N/A")
    v_time = settings.get("verify_time", "N/A")
    v_time3 = settings.get("third_verify_time", "N/A")
    tut1 = settings.get("tutorial", TUTORIAL)
    tut2 = settings.get("tutorial_2", TUTORIAL_2)
    tut3 = settings.get("tutorial_3", TUTORIAL_3)
    s_log = settings.get("log", "N/A")
    s_fsub = settings.get("fsub") or settings.get("fsub_id", "N/A")
    s_tmpl = settings.get("template", "N/A")
    s_cap = settings.get("caption", "N/A")

    out = (
        f"<b>⚙️ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ꜰᴏʀ - {title}</b>\n\n"
        f"✅️ <b><u>1sᴛ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>\n"
        f"<b>ɴᴀᴍᴇ</b> - <code>{s_short}</code>\n"
        f"<b>ᴀᴘɪ</b> - <code>{s_api}</code>\n\n"
        f"✅️ <b><u>2ɴᴅ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>\n"
        f"<b>ɴᴀᴍᴇ</b> - <code>{s_short2}</code>\n"
        f"<b>ᴀᴘɪ</b> - <code>{s_api2}</code>\n\n"
        f"✅️ <b><u>𝟹ʀᴅ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>\n"
        f"<b>ɴᴀᴍᴇ</b> - <code>{s_short3}</code>\n"
        f"<b>ᴀᴘɪ</b> - <code>{s_api3}</code>\n\n"
        f"⏰ <b>2ɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ</b> - <code>{v_time}</code>\n"
        f"⏰ <b>𝟹ʀᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ</b> - <code>{v_time3}</code>\n\n"
        f"1️⃣ <b>ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ 1</b> - {tut1}\n"
        f"2️⃣ <b>ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ 2</b> - {tut2}\n"
        f"3️⃣ <b>ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ 3</b> - {tut3}\n\n"
        f"📝 <b>ʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ</b> - <code>{s_log}</code>\n"
        f"🚫 <b>ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ ɪᴅ</b> - <code>{s_fsub}</code>\n\n"
        f"🎯 <b>ɪᴍᴅʙ ᴛᴇᴍᴘʟᴀᴛᴇ</b> - <code>{s_tmpl}
