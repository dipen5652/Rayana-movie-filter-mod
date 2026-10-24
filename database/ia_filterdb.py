
import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from typing import Dict, List
from collections import defaultdict
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from utils import get_settings, save_group_settings
from info import (
    COLLECTION_NAME, COVERX, DATABASE_NAME, DATABASE_URI, DATABASE_URI2,
    INDEX_CAPTION, MAX_B_TN, MULTIPLE_DB, ULTRA_FAST_MODE, USE_CAPTION_FILTER,
)
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache


logger = logging.getLogger(__name__)
# ---------------------------------------------------------

# Global cache for DB size
_db_stats_cache = {"timestamp": None, "primary_size": 0.0}

@lru_cache(maxsize=4096)
def compile_regex(pattern):
    return re.compile(pattern, re.IGNORECASE)

# --- PROBLEM 1 FIX: Sirf zarurat ka change ---
def normalize_query(text: str) -> str:
    # 1. camelCase split: visionQuest -> vision Quest
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # 2. Saare symbols ko space: & ' , _ - . + # $ % ^ * ( ) ! ~ ` , ; : " ' ? / < > [ ] { } = | \
    text = re.sub(r"[_\-\.#+$%^&*()!~`,;:\"'?/<\>\[\]{}=|\\]", " ", text)
    # 3. Multiple spaces -> single
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Primary DB
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

# secondary db
if MULTIPLE_DB and DATABASE_URI2:
    client2 = AsyncIOMotorClient(DATABASE_URI2)
    db2 = client2[DATABASE_NAME]
    instance2 = Instance.from_db(db2)
else:
    client2 = client
    db2 = db
    instance2 = instance


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute="_id")
    file_unique_id = fields.StrField(allow_none=True)
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    cover = fields.StrField(allow_none=True)

    class Meta:
        indexes = ("$file_name",)
        collection_name = COLLECTION_NAME


@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute="_id")
    file_unique_id = fields.StrField(allow_none=True)
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    cover = fields.StrField(allow_none=True)


    class Meta:
        indexes = ("$file_name",)
        collection_name = COLLECTION_NAME


async def check_db_size(db):
    try:
        now = datetime.utcnow()
        cache_stale_by_time = _db_stats_cache["timestamp"] is None or (
            now - _db_stats_cache["timestamp"] > timedelta(minutes=10)
        )
        refresh_if_size_threshold = _db_stats_cache["primary_size"] >= 10.0
        if not cache_stale_by_time and not refresh_if_size_threshold:
            return _db_stats_cache["primary_size"]
        stats = await db.command("dbstats")
        db_logical_size = stats["dataSize"]
        db_index_size = stats["indexSize"]
        db_logical_size_mb = db_logical_size / (1024 * 1024)
        db_index_size_mb = db_index_size / (1024 * 1024)
        db_size_mb = db_logical_size_mb + db_index_size_mb
        _db_stats_cache["primary_size"] = db_size_mb
        _db_stats_cache["timestamp"] = now
        return db_size_mb
    except Exception:
        logger.exception("Error checking database size")
        return 0


async def save_file(media):
    """Save file in database, with detailed logging."""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_unique_id = getattr(media, "file_unique_id", None)
    # PROBLEM 1 FIX: camelCase split + symbols -> space (1 line add)
    file_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', str(media.file_name))
    file_name = re.sub(
        r"[_\-\.#+$%^&*()!~`,;:\"'?/<\>\[\]{}=|\\]", " ", file_name
    )
    file_name = re.sub(r"\s+", " ", file_name).strip()
    saveMedia = Media
    target_db = "Primary"
    duplicate_filter = {"$or": [{"file_id": file_id}]}
    if file_unique_id:
        duplicate_filter["$or"].append({"file_unique_id": file_unique_id})
    try:
        exists = await Media.find_one(duplicate_filter)
        if exists:
            logger.info(f"[SKIP] '{file_name}' already in Primary DB.")
            return False, 0
        if MULTIPLE_DB:
            exists = await Media2.find_one(duplicate_filter)
            if exists:
                logger.info(f"[SKIP] '{file_name}' already in Secondary DB.")
                return False, 0
    except Exception as e:
        logger.error("Error during duplicate check; continuing with save.", exc_info=e)

    if MULTIPLE_DB:
        try:
            primary_db_size = await check_db_size(db)
            if primary_db_size >= 407:
                saveMedia = Media2
                target_db = "Secondary"
                logger.warning("Switching to Secondary DB due to size threshold.")
        except Exception as e:
            logger.error(
                "Error during MULTIPLE_DB check; defaulting to primary DB.", exc_info=e
            )
    try:
        cover_media = getattr(media, "video_cover", None) or getattr(media, "cover", None)
        cover_to_use = getattr(cover_media, "file_id", None)
        record = saveMedia(
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=(media.caption.html if media.caption and INDEX_CAPTION else None),
            cover=cover_to_use if COVERX else None,
        )
    except Exception as e:
        logger.exception(f"[ERROR] '{file_name}' → {e}")
        return False, 2
    try:
        await record.commit()
    except DuplicateKeyError:
        logger.info(
            f"[SKIP] DuplicateKey: '{file_name}' already exists in {target_db} DB."
        )
        return False, 0
    except Exception as e:
        logger.exception(
            f"[ERROR] Failed commit of '{file_name}' to {target_db} DB.", exc_info=e
        )
        return False, 3
    #logger.info(f"[SUCCESS] '{file_name}' saved to {target_db} DB.")
    return True, 1

async def get_search_results(chat_id, query, file_type=None, max_results=None, offset=0, filter=False):
    if max_results is None:
        if chat_id is not None:
            settings = await get_settings(int(chat_id))
            if "max_btn" not in settings:
                await save_group_settings(int(chat_id), "max_btn", True)
                settings["max_btn"] = True
            max_results = 10 if settings["max_btn"] else int(MAX_B_TN)
        else:
            max_results = int(MAX_B_TN)
    if isinstance(query, list):
        # List query ke liye bhi normalize
        normalized_list = [normalize_query(q) for q in query if q and q.strip()]
        raw_pattern = "|".join(re.escape(q) for q in normalized_list if q)
        if not raw_pattern:
            return [], None, 0
        regex = compile_regex(raw_pattern)
        if USE_CAPTION_FILTER:
            filter_mongo = {"$or": [{"file_name": regex},{"caption": regex},]}
        else:
            filter_mongo = {"file_name": regex}
    else:
        query = query.strip()
        if not query:
            return [], None, 0
        # PROBLEM 1 FIX: Query ko normalize karo
        normalized = normalize_query(query)
        if not normalized:
            return [], None, 0
        merged = normalized.replace(" ", "")
        # Dono forms ke liye pattern
        if " " in normalized:
            words = [re.escape(w) for w in normalized.split() if w]
            pattern_spaced = r".*[\s\.\+\-_ ]".join(words) if words else r"."
            # Purane files ke liye merged form bhi
            pattern_merged = re.escape(merged)
            raw_pattern = f"({pattern_spaced})|({pattern_merged})"
        else:
            raw_pattern = r"(\b|[\.\+\-_ ])" + re.escape(normalized) + r"(\b|[\.\+\-_ ])"
            # Agar single word hai toh camelCase merged bhi check (visionQuest case)
            if merged.lower() != normalized.lower():
                raw_pattern = f"({raw_pattern})|({re.escape(merged)})"
        try:
            regex = compile_regex(raw_pattern)
        except re.error:
            return [], None, 0
        if USE_CAPTION_FILTER:
            filter_mongo = { "$or": [{"file_name": regex}, {"caption": regex},]}
        else:
            filter_mongo = {"file_name": regex}

    if file_type:
        filter_mongo["file_type"] = file_type

    if ULTRA_FAST_MODE:
        limit = max_results + 1
        if MULTIPLE_DB:
            fetch_limit = offset + limit
            results = await asyncio.gather(
                Media.find(filter_mongo).sort("$natural", -1).limit(fetch_limit).to_list(length=fetch_limit),
                Media2.find(filter_mongo).sort("$natural", -1).limit(fetch_limit).to_list(length=fetch_limit),
            )
            files = results[1] + results[0]
            files = files[offset:offset + limit]
        else:
            files = await Media.find(filter_mongo).sort("$natural", -1).skip(offset).limit(limit).to_list(length=limit)
        has_next_page = len(files) > max_results
        if has_next_page:
            files = files[:-1]
        next_offset = offset + len(files) if has_next_page else ""
        total_results = offset + len(files) + (1 if has_next_page else 0)
    else:
        if MULTIPLE_DB:
            fetch_limit = offset + max_results
            count_results, find_results = await asyncio.gather(
                asyncio.gather(Media.count_documents(filter_mongo), Media2.count_documents(filter_mongo)),
                asyncio.gather(
                    Media.find(filter_mongo).sort("$natural", -1).limit(fetch_limit).to_list(length=fetch_limit),
                    Media2.find(filter_mongo).sort("$natural", -1).limit(fetch_limit).to_list(length=fetch_limit),
                )
            )
            total_results = sum(count_results)
            files = find_results[1] + find_results[0]
            files = files[offset:offset + max_results]
        else:
            total_results = await Media.count_documents(filter_mongo)
            files = await Media.find(filter_mongo).sort("$natural", -1).skip(offset).limit(max_results).to_list(length=max_results)
        next_offset = offset + len(files)
        if next_offset >= total_results:
            next_offset = ""
    return files, next_offset, total_results

async def get_bad_files(query, file_type=None):
    query = query.strip()
    if not query:
        return [], 0
    # PROBLEM 1 FIX: Normalize
    normalized = normalize_query(query)
    if not normalized:
        return [], 0
    if " " not in normalized:
        raw_pattern = r"(\b|[\.\+\-_ ])" + re.escape(normalized) + r"(\b|[\.\+\-_ ])"
    else:
        raw_pattern = r".*[\s\.\+\-_ ]".join(map(re.escape, normalized.split()))
    try:
        regex = compile_regex(raw_pattern)
    except re.error:
        return [], 0
    if USE_CAPTION_FILTER:
        filter_mongo = {
            "$or": [
                {"file_name": regex},
                {"caption": regex}
            ]
        }
    else:
        filter_mongo = {"file_name": regex}

    if file_type:
        filter_mongo["file_type"] = file_type

    tasks = [
        Media.find(filter_mongo)
        .sort("$natural", -1)
        .to_list(300)
    ]

    if MULTIPLE_DB:
        tasks.append(
            Media2.find(filter_mongo)
            .sort("$natural", -1)
            .to_list(300)
        )
    results = await asyncio.gather(*tasks)
    if MULTIPLE_DB and len(results) > 1:
        files = results[1] + results[0]
    else:
        files = results[0]
    files = files[:300]
    return files, len(files)

async def get_file_details(query):
    filter = {"file_id": query}
    tasks = [Media.find(filter).to_list(length=1)]
    if MULTIPLE_DB:
        tasks.append(Media2.find(filter).to_list(length=1))  
    results = await asyncio.gather(*tasks)
    for filedetails in results:
        if filedetails:
            return filedetails       
    return []

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash,
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

async def dreamxbotz_clean_title(filename: str, is_series: bool = False) -> str:
    try:
        year_match = re.search(r"^(.*?(\d{4}|\(\d{4}\)))", filename, re.IGNORECASE)
        if year_match:
            title = year_match.group(1).replace("(", "").replace(")", "")
            return re.sub(r"(?:@[^ \n\r\t.,:;!?()\[\]{}<>\\\/\"'=_%]+|[._\-\[\]@()]+)", " ", title).strip().title()
        if is_series:
            season_match = re.search(r"(.*?)(?:S(\d{1,2})|Season\s*(\d+)|Season(\d+))(?:\s*Combined)?", filename, re.IGNORECASE)
            if season_match:
                title = season_match.group(1).strip()
                season = season_match.group(2) or season_match.group(3) or season_match.group(4)
                title = re.sub(r"(?:@[^ \n\r\t.,:;!?()\[\]{}<>\\\/\"'=_%]+|[._\-\[\]@()]+)", " ", title).strip().title()
                return f"{title} S{int(season):02}"
        return re.sub(r"(?:@[^ \n\r\t.,:;!?()\[\]{}<>\\\/\"'=_%]+|[._\-\[\]@()]+)", " ", filename).strip().title()
    except Exception as e:
        logger.error(f"Error in truncate_title: {e}")
        return filename

async def dreamxbotz_get_movies(limit: int = 20) -> List[str]:
    try:
        cursor = await dreamxbotz_fetch_media(limit * 2)
        results = set()
        pattern = r"(?:s\d{1,2}|season\s*\d+|season\d+)(?:\s*combined)?(?:e\d{1,2}|episode\s*\d+)?\b"
        for file in cursor:
            file_name = getattr(file, "file_name", "")
            if not re.search(pattern, file_name, re.IGNORECASE):
                title = await dreamxbotz_clean_title(file_name)
                results.add(title)
            if len(results) >= limit: break
        return sorted(list(results))[:limit]
    except Exception as e:
        logger.error(f"Error in dreamxbotz_get_movies: {e}")
        return []

async def dreamxbotz_get_series(limit: int = 30) -> Dict[str, List[int]]:
    try:
        cursor = await dreamxbotz_fetch_media(limit * 5)
        grouped = defaultdict(list)
        pattern = r"(.*?)(?:S(\d{1,2})|Season\s*(\d+)|Season(\d+))(?:\s*Combined)?(?:E(\d{1,2})|Episode\s*\d+)?\b"
        for file in cursor:
            file_name = getattr(file, "file_name", "")
            match = re.search(pattern, file_name, re.IGNORECASE)
            if match:
                title = await dreamxbotz_clean_title(match.group(1), is_series=True)
                season = int(match.group(2) or match.group(3) or match.group(4))
                grouped[title].append(season)
        return {title: sorted(set(seasons))[:10] for title, seasons in grouped.items() if seasons}
    except Exception as e:
        logger.error(f"Error in dreamxbotz_get_series: {e}")
        return []

# ----------------- QUALITY SCANNER LOGIC ----------------- #
async def get_duplicate_quality_movies():
    cam_pattern = re.compile(r"\b(cam|camrip|predvd|hdcam|hdts|theatre|telesync|ts|dvdscr)\b", re.IGNORECASE)
    hd_pattern = re.compile(r"\b(web-?dl|webrip|bluray|hdrip|bdrip|dvdrip)\b", re.IGNORECASE)

    cursor = Media.collection.find({}, {"file_name": 1})
    movie_dict = {}

    async for file in cursor:
        raw_name = file.get("file_name", "")
        if not raw_name:
            continue

        clean_name = re.sub(r"[_\.\-\[\]\(\)]", " ", raw_name)
        match_year = re.search(r"^(.*?)(19\d\d|20\d\d)", clean_name, re.IGNORECASE)
        base_title = match_year.group(1).strip().title() if match_year else clean_name.split()[0].title()

        if len(base_title) < 2:
            continue

        if base_title not in movie_dict:
            movie_dict[base_title] = {"web_dl": 0, "predvd": 0, "hdts": 0}

        low = raw_name.lower()
        if hd_pattern.search(low):
            movie_dict[base_title]["web_dl"] += 1
        elif "hdts" in low or "ts" in low:
            movie_dict[base_title]["hdts"] += 1
        elif cam_pattern.search(low):
            movie_dict[base_title]["predvd"] += 1

    duplicates = {}
    for movie, counts in movie_dict.items():
        if counts["web_dl"] > 0 and (counts["predvd"] > 0 or counts["hdts"] > 0):
            duplicates[movie] = counts

    return duplicates
    
