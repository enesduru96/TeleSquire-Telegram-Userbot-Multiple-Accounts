from dataclasses import dataclass

@dataclass
class SessionCheckResult:
    status: str
    phone_number: str
    username: str = None
    error: str = None
    until_date: str = None

@dataclass
class ClientInformation:
    number: str
    entity_id: int
    first_name: str
    last_name: str
    username: str
    session_creation_date: str
    profile_photo: str
    bio: str
    spambot_access_hash: int
    last_checked: int

@dataclass
class TelegramUserInformation:
    entity_id: int
    first_name: str
    last_name: str
    username: str
    about: str
    last_status: str
    is_premium: bool
    is_bot: bool

@dataclass
class TelegramUserAccessInformation:
    entity_id: int
    access_hash: int
    indexer_id: int
    indexer_phone: int

@dataclass
class ChannelInformation:
    entity_id: int
    username: str
    title: str
    about: str
    is_broadcast: bool
    is_megagroup: bool
    linked_chat_id: int
    can_view_participants: bool
    participant_count: int
    slow_mode: bool
    slow_time: int
    request_needed: bool
    is_private: bool
    invite_link: str

@dataclass
class ChannelAccessInformation:
    entity_id: int
    access_hash: int
    indexer_id: int
    indexer_phone: int
    has_joined: bool