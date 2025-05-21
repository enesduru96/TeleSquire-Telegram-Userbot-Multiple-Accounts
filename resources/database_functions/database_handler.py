import time, json, os
from sqlalchemy import select, update
from resources.database_functions.base_db_models import IndexedSession, IndexedChannel, IndexedChannelAccess, Device, SystemVersion, AppVersion, RandomDeviceOrder, SessionDuo, DialogueFiles
from resources.database_functions.base_db_models import IndexedUser, IndexedUserAccess
from resources.database_functions.base_data_classes import SessionCheckResult, ClientInformation, ChannelInformation, ChannelAccessInformation, TelegramUserInformation, TelegramUserAccessInformation
from resources._config import Config
from resources._loggers import database_logger
from resources._utils import print_green, print_red, print_blue
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncConnection
from sqlalchemy import inspect, text
from resources.database_functions.base_db_models import Base
from sqlalchemy.orm import sessionmaker

class DatabaseHandler:
    def __init__(self):
        self.config = Config()
        self.database_url = self.config.get_database_url()
        self.SessionMaker = None
        self.engine = None

    async def async_init(self):
        self.SessionMaker, self.engine = await self.initialize_database(self.database_url)
        return self

    @classmethod
    async def create(cls):
        instance = cls()
        return await instance.async_init()
    
    async def initialize_database(self, database_url: str):
        engine = create_async_engine(
            database_url, 
            echo=False
        )
        try:
            async with engine.connect() as connection:
                inspector = await connection.run_sync(inspect)
                existing_tables = await connection.run_sync(
                    lambda conn: set(inspect(conn).get_table_names())
                )

                defined_tables = set(Base.metadata.tables.keys())
                missing_tables = defined_tables - existing_tables
                if missing_tables:
                    print(f"Creating missing tables: {missing_tables}")
                    await connection.run_sync(Base.metadata.create_all)

                for table_name in defined_tables & existing_tables:
                    await self._sync_columns_and_indexes(connection, table_name)

            session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            return session_maker, engine

        except SQLAlchemyError as e:
            print(f"Database initialization error: {e}")
            raise

    async def _sync_columns_and_indexes(self, connection: AsyncConnection, table_name: str):
        inspector = await connection.run_sync(inspect)

        existing_columns = await connection.run_sync(
            lambda conn: {col["name"] for col in inspect(conn).get_columns(table_name)}
        )
        existing_indexes = await connection.run_sync(
            lambda conn: {index["name"] for index in inspect(conn).get_indexes(table_name)}
        )

        defined_columns = {col.name for col in Base.metadata.tables[table_name].columns}
        missing_columns = defined_columns - existing_columns

        defined_indexes = {index.name for index in Base.metadata.tables[table_name].indexes}
        missing_indexes = defined_indexes - existing_indexes

        for column in missing_columns:
            column_obj = Base.metadata.tables[table_name].columns[column]
            column_type = column_obj.type
            default_value = column_obj.default.arg if column_obj.default else "NULL"
            print(f"Adding column '{column}' to table '{table_name}'")
            await connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
            )
            await connection.execute(
                text(f"UPDATE {table_name} SET {column} = {default_value}")
            )

        for index_name in missing_indexes:
            index = next(
                idx for idx in Base.metadata.tables[table_name].indexes if idx.name == index_name
            )
            column_names = ", ".join(col.name for col in index.columns)
            print(f"Adding index '{index_name}' to table '{table_name}' on columns ({column_names})")
            await connection.execute(
                text(f"CREATE INDEX {index_name} ON {table_name} ({column_names})")
            )


    async def is_entity_in_db(self, model, **filters):
        async with self.SessionMaker() as db_session:
            result = await db_session.execute(select(model).filter_by(**filters))
            return result.scalars().first() is not None
    
    async def is_session_in_db(self, phone_number: str) -> bool:
        async with self.SessionMaker() as db_session:
            result = await db_session.execute(select(IndexedSession).filter_by(number=phone_number))
            return result.scalars().first() is not None

    async def is_channel_in_db(self, entity_id: int) -> bool:
        async with self.SessionMaker() as db_session:
            result = await db_session.execute(select(IndexedChannel).filter_by(entity_id=entity_id))
            return result.scalars().first() is not None

    async def is_channel_access_in_db(self, entity_id, indexer_id):
        async with self.SessionMaker() as db_session:
            result = await db_session.execute(select(IndexedChannelAccess).filter_by(entity_id=entity_id, indexer_id=indexer_id))
            return result.scalars().first() is not None
    
    async def is_user_access_in_db(self, entity_id, indexer_id):
        async with self.SessionMaker() as db_session:
            result = await db_session.execute(select(IndexedUserAccess).filter_by(entity_id=entity_id, indexer_id=indexer_id))
            return result.scalars().first() is not None

    async def save_session_info(self, client_info: ClientInformation):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    print_blue(f"Processing session for: {client_info.number}")
                    result = await db_session.execute(
                        select(IndexedSession).filter_by(entity_id=client_info.entity_id)
                    )
                    existing_session = result.scalars().first()

                    if existing_session:
                        for field in [
                            "number", "first_name", "last_name", "username", "session_creation_date",
                            "profile_photo", "bio", "spambot_access_hash", "last_checked"
                        ]:
                            setattr(existing_session, field, getattr(client_info, field))
                        existing_session.is_busy = False
                        print_green(f"Session {client_info.number} updated successfully.")
                    else:
                        db_session.add(
                            IndexedSession(
                                number=client_info.number,
                                entity_id=client_info.entity_id,
                                first_name=client_info.first_name,
                                last_name=client_info.last_name,
                                username=client_info.username,
                                session_creation_date=client_info.session_creation_date,
                                profile_photo=client_info.profile_photo,
                                bio=client_info.bio,
                                spambot_access_hash=client_info.spambot_access_hash,
                                last_checked=client_info.last_checked,
                                is_busy=False
                            )
                        )
                        print_green(f"Session {client_info.number} added successfully.")
                    return True
                except Exception as error:
                    print_red(f"Error processing session {client_info.number}: {error}")
                    database_logger.error(f"Error on 'save_session_info':\n{error}", exc_info=False)
                    return False
        
    async def update_session_last_checked(self, phone_number: str, check_time: int):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(IndexedSession).filter_by(number=phone_number)
                    )
                    session_info = result.scalars().first()
                    if session_info:
                        session_info.last_checked = check_time
                except Exception as error:
                    database_logger.error(f"Error on 'update_session_last_checked':\n{error}", exc_info=True)

    async def check_session_last_checked(self, phone_number: str) -> bool:
        try:
            one_hour_in_seconds = 3600
            current_time = int(time.time())
            async with self.SessionMaker() as db_session:
                result = await db_session.execute(
                    select(IndexedSession).filter_by(number=phone_number)
                )
                session_info = result.scalars().first()
                if session_info and session_info.last_checked:
                    return (current_time - session_info.last_checked) > one_hour_in_seconds
                return True
        except Exception as error:
            database_logger.error(f"Error on 'check_session_last_checked':\n{error}", exc_info=False)

    async def get_session_info(self, phone_number: str):
        async with self.SessionMaker() as db_session:
            try:
                result = await db_session.execute(
                    select(IndexedSession).filter_by(number=phone_number)
                )
                session_info = result.scalars().first()
                if session_info:
                    return ClientInformation(
                        number=session_info.number,
                        entity_id=session_info.entity_id,
                        first_name=session_info.first_name,
                        last_name=session_info.last_name,
                        username=session_info.username,
                        session_creation_date=session_info.session_creation_date,
                        profile_photo=session_info.profile_photo,
                        bio=session_info.bio,
                        spambot_access_hash=session_info.spambot_access_hash,
                        last_checked=session_info.last_checked
                    )
                return None
            except Exception as error:
                print_red(f"Error retrieving session info for {phone_number}: {error}")
                database_logger.error(f"Error on 'get_session_info':\n{error}", exc_info=False)
                return None
    
    async def get_session_entity_id(self, phone_number: str) -> int | None:
        async with self.SessionMaker() as db_session:
            try:
                result = await db_session.execute(
                    select(IndexedSession).filter_by(number=phone_number)
                )
                session_info = result.scalars().first()
                return session_info.entity_id if session_info else None
            except SQLAlchemyError as error:
                print_red(f"Error retrieving session entity ID for {phone_number}: {error}")
                database_logger.error(f"Error on 'get_session_entity_id':\n{error}", exc_info=False)
                return None

    async def set_session_banned(self, phone_number: str):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(IndexedSession).filter_by(number=phone_number)
                    )
                    session = result.scalars().first()

                    if session:
                        session.is_banned = True
                        print_red(f"Session {phone_number} marked as banned.")
                    else:
                        print_red(f"Session with phone number {phone_number} not found.")
                except Exception as error:
                    print_red(f"Error setting session as banned for {phone_number}: {error}")
                    database_logger.error(f"Error on 'set_session_banned':\n{error}", exc_info=False)




    async def update_session_duo(self, duo_entry: SessionDuo):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(SessionDuo).filter_by(
                            session_a_id=duo_entry.session_a_id,
                            session_b_id=duo_entry.session_b_id
                        )
                    )
                    existing_entry = result.scalars().first()

                    if existing_entry:
                        updated = False
                        if existing_entry.session_a_phone != duo_entry.session_a_phone:
                            existing_entry.session_a_phone = duo_entry.session_a_phone
                            updated = True
                        if existing_entry.session_b_phone != duo_entry.session_b_phone:
                            existing_entry.session_b_phone = duo_entry.session_b_phone
                            updated = True
                        if existing_entry.dialogue_filename != duo_entry.dialogue_filename:
                            existing_entry.dialogue_filename = duo_entry.dialogue_filename
                            updated = True

                        if updated:
                            print(f"Updated duo for session_a_id {duo_entry.session_a_id} and session_b_id {duo_entry.session_b_id}")
                    else:
                        db_session.add(duo_entry)
                        print(f"Added new duo for session_a_id {duo_entry.session_a_id} and session_b_id {duo_entry.session_b_id}")

                except Exception as e:
                    print(f"Error in update_session_duo: {e}")
                    database_logger.error(f"Error in update_session_duo: {e}", exc_info=True)

    async def create_dialogue_database(self):
        dialogue_files = [
            file.replace(".json", "") for file in os.listdir("_files/dialogues") if file.endswith(".json")
        ]

        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    for file_name in dialogue_files:
                        result = await db_session.execute(
                            select(DialogueFiles).filter_by(file_name=file_name)
                        )
                        dialogue = result.scalars().first()

                        if not dialogue:
                            db_session.add(DialogueFiles(file_name=file_name, used_count=0))
                            print_green(f"Dialogue file '{file_name}' added to the database.")

                except Exception as error:
                    print_red(f"Error creating dialogue database: {error}")
                    database_logger.error(f"Error on 'create_dialogue_database':\n{error}", exc_info=False)

    async def increment_dialogue_use(self, file_name: str):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(DialogueFiles).filter_by(file_name=file_name)
                    )
                    dialogue = result.scalars().first()

                    if dialogue:
                        dialogue.used_count += 1
                        print_green(f"Dialogue file '{file_name}' usage count incremented.")
                    else:
                        print_red(f"Dialogue file '{file_name}' not found in the database.")
                except Exception as error:
                    print_red(f"Error incrementing usage count for dialogue '{file_name}': {error}")
                    database_logger.error(f"Error on 'increment_dialogue_use':\n{error}", exc_info=False)

    async def get_least_used_dialogues(self):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(DialogueFiles.used_count).order_by(DialogueFiles.used_count.asc()).limit(1)
                    )
                    min_used_count = result.scalars().first()

                    if min_used_count is not None:
                        result = await db_session.execute(
                            select(DialogueFiles).filter_by(used_count=min_used_count)
                        )
                        dialogues = result.scalars().all()

                        print_green(f"Least used dialogues retrieved with used_count = {min_used_count}.")
                        return dialogues
                    else:
                        print_red("No dialogue files found in the database.")
                        return []
                except Exception as error:
                    print_red(f"Error retrieving least used dialogues: {error}")
                    database_logger.error(f"Error on 'get_least_used_dialogues':\n{error}", exc_info=False)
                    return []





    async def cache_new_channel(self, channel_info: ChannelInformation):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(IndexedChannel).filter_by(entity_id=channel_info.entity_id)
                    )
                    existing_channel = result.scalars().first()

                    if existing_channel:
                        updated = False
                        for field in [
                            "username", "title", "about", "is_broadcast", "is_megagroup",
                            "linked_chat_id", "can_view_participants", "participant_count",
                            "slow_mode", "slow_time", "request_needed", "is_private", "invite_link"
                        ]:
                            old_value = getattr(existing_channel, field)
                            new_value = getattr(channel_info, field)

                            if old_value != new_value:
                                setattr(existing_channel, field, new_value)
                                updated = True

                        if updated:
                            print(f"Updated channel: {channel_info.username}|{channel_info.entity_id}")
                        else:
                            print(f"Channel is already cached and up-to-date: {channel_info.username}|{channel_info.entity_id}")
                    else:
                        db_session.add(
                            IndexedChannel(
                                entity_id=channel_info.entity_id,
                                username=channel_info.username,
                                title=channel_info.title,
                                about=channel_info.about,
                                is_broadcast=channel_info.is_broadcast,
                                is_megagroup=channel_info.is_megagroup,
                                linked_chat_id=channel_info.linked_chat_id,
                                can_view_participants=channel_info.can_view_participants,
                                participant_count=channel_info.participant_count,
                                slow_mode=channel_info.slow_mode,
                                slow_time=channel_info.slow_time,
                                request_needed=channel_info.request_needed,
                                is_private=channel_info.is_private,
                                invite_link=channel_info.invite_link,
                            )
                        )
                        print_green(f"New channel cached: {channel_info.username}|{channel_info.entity_id}")
                except Exception as error:
                    print_red(f"Error caching channel {channel_info.username}|{channel_info.entity_id}: {error}")
                    database_logger.error(f"Error on 'cache_new_channel':\n{error}", exc_info=False)

    async def cache_new_channel_access(self, channel_access_info: ChannelAccessInformation):
        if await self.is_channel_access_in_db(channel_access_info.entity_id, channel_access_info.indexer_id):
            return
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    db_session.add(
                        IndexedChannelAccess(
                            entity_id=channel_access_info.entity_id,
                            access_hash=channel_access_info.access_hash,
                            indexer_id=channel_access_info.indexer_id,
                            indexer_phone=channel_access_info.indexer_phone,
                            has_joined=channel_access_info.has_joined
                        )
                    )
                    print_green(f"Channel access cached: {channel_access_info.entity_id}|{channel_access_info.indexer_phone}")
                except SQLAlchemyError as error:
                    print_red(f"Error caching channel access {channel_access_info.entity_id}|{channel_access_info.indexer_phone}: {error}")
                    database_logger.error(f"Error on 'cache_new_channel_access':\n{error}", exc_info=False)

    async def get_cached_channel_access(self, phone_number, input_value):
        async with self.SessionMaker() as db_session:
            try:
                input_value = input_value.strip()
                query = None

                if input_value.startswith("https://t.me/+"):
                    query = select(IndexedChannel).filter_by(invite_link=input_value)
                elif input_value.startswith("https://t.me/"):
                    username = input_value.split("https://t.me/")[-1].split("?")[0]
                    query = select(IndexedChannel).filter_by(username=username)
                else:
                    query = select(IndexedChannel).filter_by(username=input_value)

                result = await db_session.execute(query)
                channel = result.scalars().first()

                if not channel and not input_value.startswith("https://t.me/"):

                    result = await db_session.execute(
                        select(IndexedChannel).filter(
                            IndexedChannel.title.ilike(f"%{input_value}%")
                        )
                    )
                    channel = result.scalars().first()

                if channel:
                    result = await db_session.execute(
                        select(IndexedChannelAccess).filter_by(
                            entity_id=channel.entity_id, indexer_phone=phone_number
                        )
                    )
                    channel_access = result.scalars().first()

                    if channel_access:
                        print_green(f"[{phone_number}] - Found channel access for {input_value}")
                        return channel_access
                    else:
                        print_red(f"[{phone_number}] - {input_value}, no access.")
                        return None
                else:
                    print_red(f"No matching channel found for {input_value}.")
                    return None
            except SQLAlchemyError as error:
                print_red(f"Error in get_cached_channel_access: {error}")
                database_logger.error(f"Error on 'get_cached_channel_access':\n{error}", exc_info=False)
                return None


    async def cache_new_user(self, user_info: TelegramUserInformation):
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    result = await db_session.execute(
                        select(IndexedUser).filter_by(entity_id=user_info.entity_id)
                    )
                    existing_user = result.scalars().first()

                    if existing_user:
                        updated = False
                        for field in [
                            "first_name", "last_name", "username", "about",
                            "is_premium", "last_status", "is_bot"
                        ]:
                            old_value = getattr(existing_user, field)
                            new_value = getattr(user_info, field)

                            if old_value != new_value:
                                setattr(existing_user, field, new_value)
                                updated = True

                        if updated:
                            print(f"Updated channel: {user_info.username}|{user_info.entity_id}")
                        else:
                            print(f"Channel is already cached and up-to-date: {user_info.username}|{user_info.entity_id}")
                    else:
                        db_session.add(
                            IndexedUser(
                                    entity_id = user_info.entity_id,
                                    first_name = user_info.first_name,
                                    last_name = user_info.last_name,
                                    username = user_info.username,
                                    about = user_info.about,
                                    is_premium = user_info.is_premium,
                                    last_status = user_info.last_status,
                                    is_bot = user_info.is_bot
                            )
                        )
                        print_green(f"New User cached: {user_info.username}|{user_info.entity_id}")
                except Exception as error:
                    print_red(f"Error caching user {user_info.username}|{user_info.entity_id}: {error}")
                    database_logger.error(f"Error on 'cache_new_user':\n{error}", exc_info=False)

    async def cache_new_user_access(self, user_access_info: TelegramUserAccessInformation):
        if await self.is_user_access_in_db(user_access_info.entity_id, user_access_info.indexer_id):
            return
        async with self.SessionMaker() as db_session:
            async with db_session.begin():
                try:
                    db_session.add(
                        IndexedUserAccess(
                            entity_id=user_access_info.entity_id,
                            access_hash=user_access_info.access_hash,
                            indexer_id=user_access_info.indexer_id,
                            indexer_phone=user_access_info.indexer_phone,
                        )
                    )
                    print_green(f"User access cached: {user_access_info.entity_id}|{user_access_info.indexer_phone}")
                except SQLAlchemyError as error:
                    print_red(f"Error caching user access {user_access_info.entity_id}|{user_access_info.indexer_phone}: {error}")
                    database_logger.error(f"Error on 'cache_new_user_access':\n{error}", exc_info=False)

    async def get_cached_user_access(self, phone_number, input_value):
        async with self.SessionMaker() as db_session:
            try:
                input_value = input_value.strip()
                query = None

                if isinstance(input_value, int):
                    query = select(IndexedUser).filter_by(entity_id=input_value)
                elif isinstance(input_value, str):
                    input_value = input_value.replace("@","")
                    query = select(IndexedUser).filter_by(username=input_value)

                result = await db_session.execute(query)
                user = result.scalars().first()

                if user:
                    result = await db_session.execute(
                        select(IndexedUserAccess).filter_by(
                            entity_id=user.entity_id, indexer_phone=phone_number
                        )
                    )
                    user_access = result.scalars().first()

                    if user_access:
                        print_green(f"[{phone_number}] - Found user access for {input_value}")
                        return user_access
                    else:
                        print_red(f"[{phone_number}] - {input_value}, no access.")
                        return None
                else:
                    print_red(f"No matching user found for {input_value}.")
                    return None
            except SQLAlchemyError as error:
                print_red(f"Error in get_cached_user_access: {error}")
                database_logger.error(f"Error on 'get_cached_user_access':\n{error}", exc_info=False)
                return None








async def debug_show_tables(database_url):
    """
    Veritabanındaki mevcut tabloları ve sütunları gösterir (asenkron).
    """
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        inspector = await connection.run_sync(inspect)
        tables = await connection.run_sync(lambda conn: inspector.get_table_names())

        print("Existing tables in the database:")
        for table in tables:
            print(f"- {table}")
            columns = await connection.run_sync(lambda conn: inspector.get_columns(table))
            for column in columns:
                print(f"    {column['name']} ({column['type']})")

async def debug_print_sessions(database_url, row_limit=30):
    """
    'sessions' tablosunun yapısını ve örnek verilerini gösterir (asenkron).
    """
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        inspector = await connection.run_sync(inspect)
        if "sessions" not in await connection.run_sync(lambda conn: inspector.get_table_names()):
            print("The 'sessions' table does not exist in the database.")
            return

        print("Structure of the 'sessions' table:")
        columns = await connection.run_sync(lambda conn: inspector.get_columns("sessions"))
        column_names = [column["name"] for column in columns]
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")

        print("\nIndexes on the 'sessions' table:")
        indexes = await connection.run_sync(lambda conn: inspector.get_indexes("sessions"))
        if indexes:
            for index in indexes:
                idx_columns = ", ".join(index['column_names'])
                print(f"  - {index['name']} on columns ({idx_columns})")
        else:
            print("  No indexes found on the 'sessions' table.")

        print(f"\nData in the 'sessions' table (up to {row_limit} rows):")
        rows = await connection.execute(text(f"SELECT * FROM sessions LIMIT {row_limit}"))
        rows = await rows.fetchall()

        print(" | ".join(column_names))
        if rows:
            for row in rows:
                print(" | ".join(str(value) if value is not None else "NULL" for value in row))
        else:
            print("No data found in the 'sessions' table.")

async def update_is_busy_nulls(database_url):
    """
    'is_busy' sütunundaki NULL değerleri 0 ile günceller (asenkron).
    """
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        print("Ensuring all NULL values in 'is_busy' column are set to 0...")
        await connection.execute(text("UPDATE sessions SET is_busy = 0 WHERE is_busy IS NULL"))
        print("Update completed.")
