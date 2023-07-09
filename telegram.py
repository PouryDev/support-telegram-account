from pyrogram import Client, types
from pyrogram.raw.functions.channels import TogglePreHistoryHidden, CreateForumTopic
from pyrogram.enums import ChatType
from pyrogram.errors import (
    RPCError, PeerIdInvalid, FloodWait, ChatAdminRequired, UserPrivacyRestricted, ChannelAddInvalid
)
import os
from logging import error
from pyrogram.enums import ChatMemberStatus
from typing import Optional, Union
from pyrogram.types import Chat


# Return started pyrogram client
async def get_client() -> Client:
    proxy = None
    if os.getenv('TELEGRAM_ACCOUNT_PROXY_ENABLED', 'True') == 'True':
        proxy = {
            'scheme': 'socks5',
            'hostname': str(os.getenv('PROXY_HOST')),
            'port': int(os.getenv('PROXY_PORT'))
        }

    app = Client('account', os.getenv("API_ID"), os.getenv("API_HASH"), proxy=proxy)
    await app.start()
    return app


# Create telegram group with given title and description
# Returns true if group created successfully and false in failure
async def create_group(title: str, description: str, welcome_text: str, pin: bool = False) -> (Optional['Chat'], str):
    # Get pyrogram client
    app = await get_client()

    try:
        # Create supergroup with given title and description
        chat = await app.create_supergroup(title, description)

        # Send welcome message
        message = await app.send_message(chat.id, welcome_text)
        if pin:
            await message.pin(disable_notification=False)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        return None, e
    # Check if group created or not
    if not isinstance(chat, types.Chat):
        return None, ''

    em = ''
    # Set group permissions
    try:
        await app.set_chat_permissions(chat.id, types.ChatPermissions(
            can_invite_users=False,
            can_change_info=False,
            can_send_polls=True,
            can_pin_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_messages=True,
            can_add_web_page_previews=True,
        ))
        TogglePreHistoryHidden(channel=chat, enabled=True)
        CreateForumTopic(channel=chat, title='Announcements', random_id=85)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        em = e

    # Stop client
    await app.stop()
    return chat, em


# Converts chat object to dictionary
def chat_to_dict(chat: Chat) -> dict:
    return {
        'id': chat.id,
        'title': chat.title,
        'description': chat.description,
    }


# Delete supergroup and return a boolean which shows if its deleted or not
async def expire_group(chat_id: Union[str, int]):
    # Get pyrogram client
    app = await get_client()

    # Delete supergroup
    try:
        boolean = await app.archive_chats([chat_id])
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        boolean = False

    try:
        await change_all_chat_members_permissions(app, chat_id)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        boolean = False
        try:
            await app.unarchive_chats([chat_id])
        except (RPCError, PeerIdInvalid) as e:
            error(e)

    # Stop client
    await app.stop()
    return boolean


# Add members to an existing group
async def add_chat_members(chat_id: Union[str, int], user_ids: Union[dict, list]) -> (bool, str):
    # Get pyrogram client
    app = await get_client()

    em = ''
    res = True

    # Add users to group
    try:
        res = await app.add_chat_members(chat_id, user_ids)
    except (RPCError, PeerIdInvalid, FloodWait, ChatAdminRequired, ChannelAddInvalid, UserPrivacyRestricted) as e:
        error(e)
        em = e
        # send_alert(f'Failed to add group members for id {chat_id}\n\n{e}')
        if len(user_ids) == 1:
            res = False

    await app.stop()
    return res, em


# Remove member from a group
async def ban_chat_member(chat_id: Union[str, int], user_id: Union[str, int]) -> (bool, str):
    # Get pyrogram client
    app = await get_client()

    em = ''

    # Ban a member from group
    try:
        res = await app.ban_chat_member(int(chat_id), int(user_id))
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        em = e
        res = False

    # Stop client
    await app.stop()
    return res, em


# Get all user groups
async def get_all_groups() -> list:
    # Get client instance
    app = await get_client()

    try:
        # Get all user chats
        dialogs = app.get_dialogs()
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return []

    # Put all groups and supergroups in groups variable
    groups = []
    async for item in dialogs:
        group = item.chat
        if group.type == ChatType.SUPERGROUP or group.type == ChatType.GROUP:
            groups.append({
                'id': group.id,
                'title': group.title,
                'description': group.description,
            })

    # Stop client
    await app.stop()

    return groups


async def get_contacts() -> list:
    app = await get_client()

    contacts = await app.get_contacts()

    await app.stop()

    response = []
    for item in contacts:
        response.append({
            'id': item.id,
            'first_name': item.first_name,
            'last_name': item.last_name,
            'username': item.username,
            'phone_number': item.phone_number,
        })

    return response


# Unarchive chat
async def unarchive(chat_id: Union[str, int]) -> (bool, str):
    # Get client instance
    app = await get_client()

    # Unarchive chat using given chat id and return false on failure
    try:
        await app.unarchive_chats([chat_id])
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return False, e

    # Grant send message permission to users
    await change_all_chat_members_permissions(app, chat_id, True)

    # Stop client
    await app.stop()

    return True, ''


# Get chat invite link
async def get_invite_link(chat_id: Union[str, int]) -> str:
    # Get telegram client instance
    app = await get_client()

    # Get invite link and return empty on failure
    try:
        link = await app.create_chat_invite_link(chat_id)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return ''

    # Stop client and return link
    await app.stop()

    return link.invite_link


# Unban user from a group
async def unban_chat_member(chat_id: Union[str, int], user_id: Union[str, int]) -> (bool, str):
    # Get telegram client instance
    app = await get_client()

    # Unban user from group and return false on failure
    try:
        await app.unban_chat_member(chat_id, user_id)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return False, e

    # Stop client
    await app.stop()

    return True, ''


# Promote member to admin
async def promote_member(chat_id: Union[str, int], user_id: Union[str, int]) -> bool:
    # Get telegram client instance
    app = await get_client()

    # Promote member to admin and return false on failure
    try:
        result = await app.promote_chat_member(chat_id=chat_id, user_id=user_id, privileges=types.ChatPrivileges(
            can_delete_messages=True,
            can_restrict_members=True,
            can_promote_members=True,
            can_invite_users=True,
            can_manage_chat=True,
            can_manage_video_chats=True,
            can_change_info=True,
            can_pin_messages=True,
            can_edit_messages=True,
            can_post_messages=True,
        ))
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return False

    # Stop client
    await app.stop()

    return result


# edit message with given message id and chat id
async def edit_message(message_id: int, chat_id: Union[str, int], message: str) -> (bool, str):
    # Get telegram client instance
    app = await get_client()

    # Edit message and return false on failure
    try:
        await app.edit_message_text(message_id=message_id, chat_id=chat_id, text=message)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return False, e

    # Stop client instance
    await app.stop()

    return True, ''


# delete message with given message id and chat id
async def delete_message(message_id: int, chat_id: Union[str, int]) -> (bool, str):
    # Get telegram client instance
    app = await get_client()

    # Delete message and return false on failure
    try:
        await app.delete_messages(chat_id=chat_id, message_ids=message_id)
    except (RPCError, PeerIdInvalid) as e:
        error(e)
        await app.stop()
        return False, e

    # Stop client
    await app.stop()

    return True, ''


# Change chat permissions in telegram app
async def change_all_chat_members_permissions(client: Client, chat_id: str, can_send_message: bool = False) -> bool:
    # Get all chat members
    members = client.get_chat_members(chat_id)

    # Change permissions for each member
    async for member in members:
        # Skip if member is admin or owner or in exceptions
        if member.status == ChatMemberStatus.ADMINISTRATOR \
                or member.status == ChatMemberStatus.OWNER:
            continue
        try:
            await client.restrict_chat_member(
                chat_id=chat_id,
                user_id=member.user.id,
                permissions=types.ChatPermissions(
                    can_send_messages=can_send_message,
                    can_send_media_messages=can_send_message,
                    can_add_web_page_previews=can_send_message,
                )
            )
        except (RPCError, PeerIdInvalid) as e:
            error(e)
            error(f'Failed to change permissions for {member.user.id} in chat {chat_id}')
            return False

    return True


async def revoke_chat_invite_links(chat_id: Union[int, str]):
    # Get client instance
    app = await get_client()

    # Get bot chat id
    me = await app.get_me()

    # Get all chat invite links
    links = app.get_chat_admin_invite_links(chat_id, me.id)
    async for link in links:
        if not link.is_revoked:
            try:
                await app.revoke_chat_invite_link(chat_id, link.invite_link)
            except (RPCError, PeerIdInvalid) as e:
                error(e)

    # Stop client
    await app.stop()
