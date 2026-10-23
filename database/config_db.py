from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, uri, db_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.col = self.db.user
        self.config_col = self.db.configuration
        self.pending_col = self.db.pending_requests

    async def update_top_messages(self, user_id, message_text):
        user = await self.col.find_one({"user_id": user_id, "messages.text": message_text})
        
        if not user:
            await self.col.update_one(
                {"user_id": user_id},
                {"$push": {"messages": {"text": message_text, "count": 1}}},
                upsert=True
            )
        else:
            await self.col.update_one(
                {"user_id": user_id, "messages.text": message_text},
                {"$inc": {"messages.$.count": 1}}
            )

    async def get_top_messages(self, limit=30):
        pipeline = [
            {"$unwind": "$messages"},
            {"$group": {"_id": "$messages.text", "count": {"$sum": "$messages.count"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = await self.col.aggregate(pipeline).to_list(limit)
        return [result['_id'] for result in results]
    
    async def delete_all_messages(self):
        await self.col.delete_many({})

    # ----------------- AUTO NOTIFY PENDING REQUESTS ----------------- #
    async def add_pending_request(self, query: str, user_id: int):
        if not query or not user_id:
            return False
        q = query.lower().strip()
        q = re.sub(r"\b(movie|movies|film|series|full|download|link|send)\b", "", q, flags=re.IGNORECASE).strip()
        q = re.sub(r"\s+", " ", q)
        if len(q) < 3:
            return False

        try:
            await self.pending_col.update_one(
                {"query": q},
                {
                    "$addToSet": {"user_ids": int(user_id)},
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving pending request: {e}")
            return False

        async def get_and_delete_pending(self, file_name: str):
        if not file_name or not isinstance(file_name, str):
            return []

        clean_file = re.sub(r"[_.\-\[\]\(\)]", " ", file_name.lower())
        clean_file = re.sub(r"\s+", " ", clean_file).strip()

        noise_pattern = r"\b(480p|720p|1080p|2160p|4k|hdr|hevc|x264|x265|bluray|webrip|hdtc|hindi|english|dubbed|esub)\b"
        clean_file_no_tags = re.sub(noise_pattern, "", clean_file, flags=re.IGNORECASE)

        matched_docs = []
        try:
            cursor = self.pending_col.find({}).sort("created_at", -1).limit(300)
            all_pending = await cursor.to_list(length=300)

            for doc in all_pending:
                q = doc.get("query", "").strip()
                if not q or len(q) < 3:
                    continue

                q_words = [w for w in q.split() if len(w) > 2 and w not in ["the", "and", "movie", "film"]]
                if not q_words:
                    q_words = [q]

                all_words_matched = all(re.search(r"\b" + re.escape(w) + r"\b", clean_file_no_tags) for w in q_words)
                if all_words_matched:
                    # find_one_and_delete use karne se duplicate parallel calls me doosri file ko ye doc nahi milega
                    deleted_doc = await self.pending_col.find_one_and_delete({"_id": doc["_id"]})
                    if deleted_doc:
                        matched_docs.append(deleted_doc)

        except Exception as e:
            logger.error(f"Error checking pending requests: {e}")

        return matched_docs

    async def get_all_pending(self):
        try:
            return await self.pending_col.find({}).sort("created_at", -1).to_list(length=100)
        except Exception as e:
            logger.error(f"Error getting pending list: {e}")
            return []

    async def delete_pending(self, query: str):
        try:
            await self.pending_col.delete_one({"query": query.lower().strip()})
        except Exception as e:
            logger.error(f"Error deleting pending: {e}")

    async def clear_all_pending(self):
        try:
            await self.pending_col.delete_many({})
        except Exception as e:
            logger.error(f"Error clearing pending: {e}")


mdb = Database(DATABASE_URI, "admin_database")
