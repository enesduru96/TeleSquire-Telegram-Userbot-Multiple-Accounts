from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, Index, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
Base = declarative_base()



#region Proxies
class Proxy(Base):
    __tablename__ = 'proxies'
    id = Column(Integer, primary_key=True)
    proxy_address = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String)
    password = Column(String)

class ProxyOrder(Base):
    __tablename__ = 'proxy_order'
    id = Column(Integer, primary_key=True)
    current_index = Column(Integer, default=0)

class FilteredProxy(Base):
    __tablename__ = "filtered_proxies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    clean = Column(Boolean, nullable=True)
    fraud_score = Column(Integer, nullable=True)
    geolocation = Column(String, nullable=True)

class ProxyUseCounter(Base):
    __tablename__ = "proxy_use_counter"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy = Column(String, nullable=False)
    used_times = Column(Integer, default=0)

#endregion

#region Random Device

class SystemVersion(Base):
    __tablename__ = 'system_versions'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class AppVersion(Base):
    __tablename__ = 'app_versions'
    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)

class RandomDeviceOrder(Base):
    __tablename__ = 'random_device_order'
    id = Column(Integer, primary_key=True)
    main_order = Column(Integer, default=0)
    system_versions_order = Column(Integer, default=0)
    devices_order = Column(Integer, default=0)
    app_version_id = Column(Integer, ForeignKey('app_versions.id'))

    app_version = relationship('AppVersion')

class MainOrder(Base):
    __tablename__ = 'main_order'
    id = Column(Integer, primary_key=True)
    order = Column(Integer, default=0)

#endregion


class IndexedSession(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    number = Column(String, nullable=False)
    entity_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    session_creation_date = Column(String, nullable=True)
    profile_photo = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    spambot_access_hash = Column(String, nullable=True)
    last_checked = Column(Integer, nullable=True)
    is_busy = Column(Boolean, nullable=False, default=False)
    is_banned = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index('ix_sessions_entity_id', 'entity_id'),
        Index('ix_sessions_number', 'number'),
    )

class IndexedUser(Base):
    __tablename__ = 'indexed_users'
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    about = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    last_status = Column(String, nullable=True)
    is_bot = Column(Boolean, default=False)

    __table_args__ = (
        Index('ix_indexed_users_entity_id', 'entity_id'),
    )

class IndexedUserAccess(Base):
    __tablename__ = 'indexed_users_access'
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False)
    access_hash = Column(String, nullable=False)
    indexer_id = Column(Integer, nullable=False)
    indexer_phone = Column(Integer, nullable=False)

    __table_args__ = (
        Index('ix_indexed_users_access_entity_id', 'entity_id'),
        Index('ix_indexed_users_access_indexer_id', 'indexer_id'),
        Index('ix_indexed_users_access_indexer_phone', 'indexer_phone'),
    )

class IndexedChannel(Base):
    __tablename__ = 'indexed_channels'
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    title = Column(String, nullable=True)
    about = Column(String, nullable=True)
    is_broadcast = Column(Boolean, default=False)
    is_megagroup = Column(Boolean, default=False)
    linked_chat_id = Column(Integer, nullable=True)
    can_view_participants = Column(Boolean, nullable=True)
    participant_count = Column(Integer, nullable=True)
    slow_mode = Column(Boolean, default=False)
    slow_time = Column(Integer, default=0)
    request_needed = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    invite_link = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_indexed_channels_entity_id', 'entity_id'),
        Index('ix_indexed_channels_invite_link', 'invite_link'),
        Index('ix_indexed_channels_username', 'username'),
    )

class IndexedChannelAccess(Base):
    __tablename__ = 'indexed_channels_access'
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False)
    access_hash = Column(String, nullable=False)
    indexer_id = Column(Integer, nullable=False)
    indexer_phone = Column(Integer, nullable=False)
    has_joined = Column(Boolean, default=False)

    __table_args__ = (
        Index('ix_indexed_channels_access_entity_id', 'entity_id'),
        Index('ix_indexed_channels_access_indexer_id', 'indexer_id'),
        Index('ix_indexed_channels_access_indexer_phone', 'indexer_phone'),
    )



class SessionDuo(Base):
    __tablename__ = 'session_duos'
    id = Column(Integer, primary_key=True)
    session_a_id = Column(Integer, nullable=False)
    session_a_phone = Column(String, nullable=False)
    session_b_id = Column(Integer, nullable=False)
    session_b_phone = Column(String, nullable=False)
    dialogue_filename = Column(String, nullable=False)


class DialogueFiles(Base):
    __tablename__ = 'session_duos_dialogues'
    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False)
    used_count = Column(Integer, default=0)


class DialogueTask(Base):
    __tablename__ = 'warmup_tasks'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    sentence_order = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    side = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)