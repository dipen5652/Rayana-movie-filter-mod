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
    
#Remove Nahi Kiya Hu.....Agar Tujha Remove Karna Hai To Kar Dena
async def old_get_poster(query, bulk=False, id=False, file=None):
    try:
        if not id:
            query = (query.strip()).lower()
            title = query
            year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1])
                title = (query.replace(year, "")).strip()
            elif file is not None:
                year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                if year:
                    year = list_to_str(year[:1]) 
            else:
                year = None
            movieid = await asyncio.to_thread(imdb.search_movie, title.lower(), results=10)
            if not movieid:
                return None
            if year:
                filtered = list(filter(lambda k: str(k.get('year')) == str(year), movieid))
                if not filtered:
                    filtered = movieid
            else:
                filtered = movieid
            movieid = list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
            if not movieid:
                movieid = filtered
            if bulk:
                return movieid
            movieid = movieid[0].movieID
        else:
            movieid = query

        movie = await asyncio.to_thread(imdb.get_movie, movieid)
        if not movie:
            return None
        await asyncio.to_thread(imdb.update, movie, info=['main', 'vote details'])
        if movie.get("original air date"):
            date = movie["original air date"]
        elif movie.get("year"):
            date = movie.get("year")
        else:
            date = "N/A"
        plot = ""
        if not LONG_IMDB_DESCRIPTION:
            plot = movie.get('plot')
            if plot and len(plot) > 0:
                plot = plot[0]
        else:
            plot = movie.get('plot outline')
        if plot and len(plot) > 800:
            plot = plot[0:800] + "..."
        STANDARD_GENRES = {
            'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary',
            'Drama', 'Family', 'Fantasy', 'Film-Noir', 'History', 'Horror', 'Music',
            'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western'
        }
        raw_genres = movie.get("genres", "N/A")
        if isinstance(raw_genres, str):
            genre_list = [g.strip() for g in raw_genres.split(",")]
            genres = ", ".join(g for g in genre_list if g in STANDARD_GENRES) or "N/A"
        else:
            genres = ", ".join(g for g in raw_genres if
