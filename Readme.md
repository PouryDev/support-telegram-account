## Telegram Support: Account Service
### Description
Telegram Support Account service is a Telegram automation that allows you to manage your Telegram account from the API. It is written in Python Flask and uses the [pyrogram](https://docs.pyrogram.org).
### Features
- [x] Send Announcements To Groups
- [x] Create Groups
- [x] Expire Groups
- [x] Add Users To Groups
- [x] Remove Users From Groups
- [x] Promote Users In Groups
- [x] Demote Users In Groups

### Installation
1. Clone the repository
```bash
git clone https://github.com/PouryDev/support-telegram-account
```
2. Install the requirements
```bash
pip intall -r requirements.txt
```
3. Add these items to your env variables
```bash
export API_ID={API_ID_GIVEN_BY_TELEGRAM}
export API_HASH={API_HASH_GIVEN_BY_TELEGRAM}
export PROXY_HOST={PROXY_HOST}
export PROXY_PORT={PROXY_PORT}
export API_KEY={API_KEY_YOU_GENERATED_BY_YOURSELF}
export TELEGRAM_ACCOUNT_PROXY_ENABLED={True_FOR_USING_PROXY_OR_False_FOR_USING_SYSTEM_PROXY}
```
4. Run the bot
```bash
python3 app.py
```
