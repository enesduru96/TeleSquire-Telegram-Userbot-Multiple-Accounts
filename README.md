
# TeleSquire Telegram Userbot Multiple Accounts

A general purpose Telegram automation tool utilizing asyncio for concurrency suitable for multiple account utilization (100s to 1000s) using Telethon library.
After a few years of comercially developing & selling telegram tools and official bots, I have decided that it was enough for me and wanted to leave one last open-source tool for people who want to learn how they can create their own Telegram automation tools. So this tool can be called an abandoned but working telegram automation tool, open source & free for anyone for educational purposes.

---
  Most people do not want to get into the chaos of creating accounts -and it has become extremely difficult with the latest Telegram updates- so they prefer to buy .session + .json formatted telegram accounts for mass use.
Therefore I've created a few scripts specifically for accounts bought from  "hstock.org", helping automate the downloading and setting up the account files process, eliminating hours of manual work on each bulk account buy.

### Features
- Mega & Zie account file downloader for accounts bought from hstock
- OOP Design to maintain code readability and clarity
- Menu System clustering related functions under menus

#### Accounts
- Account generation with LD Player android automation (using appium & adb commands) _(needs improvement)_
- Scraped and ready to use telegram names and bios
- Bulk ban checking for available accounts
- Bulk spambot hidden ban checker and complainer (with a list of generated human-like complaint sentences)
- Manual login and save account in session+json format
- Get login code from session (to login from other devices manually) <br><br>
- Bulk Convert seller session files to make their files compatible with this tool, and create new sessions from it to have a fresh and unique session
- - _Terminate other sessions (to disable the seller's session files and use the converted, generated new sessions to prevent fraud (some account sellers sell the session files to multiple customers)_
> Any kind of session file generation (acc generation or session file converting) causes the new session to start with a fully new device, app and app version information, further randomizing and humanizing the accounts)

<br>
- Bulk save account information to local database
- Bulk change profile info (name, profile picture, bio etc.)
- Bulk Assign proxies to each account separately and save them for later use
- Bulk Change Two-Factor password of accounts
- Reset Two-Factor password of accounts (applies in 7 days after reset request unless cancelled)

#### Channels
- Bulk join channel
- Bulk send view count and reactions to any channel post
- Print channel information (for developer purposes)

#### Bot interaction
- Start bot request (to increase use count and popularity of the target bot)

#### Json & Config Menu
- Change app version of session files (to update the emulated telegram android app version when a new update is pushed)
- Fix incompatible json files (some account sellers have different json formats)

#### Warmup Menu (incomplete)
- Create session duos (to later make them talk to each other to increase account integrity)
- Create dialogue tasks (incomplete)
- - The code of this feature is only a "todo", however, there are around a thousand dialogue example files in json format, feel free to utilize them when creating such a feature.


---

This tool can be used as a starting point for people who want to create a large-scale telegram tool with the help of its clear design. Anyone can extend using the same patterns and add new features like sending messages, inviting others to groups etc. (not recommended since these will cause the accounts to get banned easily)