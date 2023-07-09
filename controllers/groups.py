from flask import request
import helpers
import telegram
import os
from logging import error, info
from helpers import send_alert


headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': os.getenv('API_KEY')
}


# Create telegram group with given title and description
# params -> title(string), description(string)
async def create() -> dict:
    # Check if request method is POST
    if request.method != 'POST':
        return {'status': 405, 'message': 'method not allowed'}

    # Get json data sent to us
    data = request.json

    # Check if required fields are filled
    validated, null_fields = helpers.required(data, ['title', 'description'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    pin = 'pin' in data and data['pin']

    # Create supergroup and check if it is created or not
    chat, em = await telegram.create_group(data['title'], data['description'], data['welcome_text'], pin)
    if chat is None:
        if len(em) > 1:
            send_alert(f'{em}\n<b>Title: </b>{data["title"]}')
        return {'status': 500, 'message': 'something went wrong please contact PO or try again later'}

    # Convert chat object to dict
    chat = telegram.chat_to_dict(chat)
    # Get invite link for created group
    chat['invite_link'] = await telegram.get_invite_link(chat['id'])

    # Add bot to group and promote it to admin
    await telegram.add_chat_members(chat['id'], os.getenv('TELEGRAM_BOT_USERNAME'))
    await telegram.promote_member(chat['id'], os.getenv('TELEGRAM_BOT_USERNAME'))

    return {'status': 200, 'message': 'group created successfully', 'data': chat}


# Archive supergroup by given chat_id
# params -> chat_id(integer)
async def archive() -> dict:
    # Check if request method is POST
    if request.method != 'POST':
        return {'status': 405, 'message': 'method not allowed'}

    # Get chat id from request body and check if chat_id has been sent to us
    chat_id = request.json.get('id')
    if chat_id is None:
        return {'status': 422, 'message': 'please fill all fields'}

    # Delete telegram group and return error on failure
    if not await telegram.expire_group(chat_id):
        return {'status': 500, 'message': 'something went wrong please try again later or contact PO'}

    # Revoke invite links
    await telegram.revoke_chat_invite_links(chat_id)

    return {'status': 200, 'message': 'group archived successfully', 'data': {'chat_id': chat_id}}


# Add users to an existing group
# params -> chat_id(integer), user_ids(list)
async def add_chat_members() -> dict:
    # Check if request method is post
    if request.method != 'POST':
        return {'status': 405, 'message': 'method not allowed'}

    # Get data from request body
    data = request.json

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id', 'user_ids', 'admins'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    # Check if user_ids field is list
    if not isinstance(data['user_ids'], list):
        return {'status': 422, 'message': 'user_ids must be array'}

    user_ids = []
    for user_id in data['user_ids']:
        # Add @ to user_id if it is not there
        if user_id[0] != '@':
            user_id = '@' + user_id
        user_ids.append(user_id)

    info(f'payload: {data}')
    info(f'user_ids: {user_ids}')

    is_user_added, em = await telegram.add_chat_members(int(data['chat_id']), user_ids)
    result = {
        'result': is_user_added,
        'error': em,
    }

    info(f'result: {result}')

    # Add user to group and return error on failure
    if not is_user_added:
        send_alert(f'{em}\n<b>Group id: </b>{data["chat_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later or contact PO'}

    # Promote admin agents to chat admin in telegram group
    for admin_id in data['admins']:
        try:
            await telegram.promote_member(data['chat_id'], admin_id)
        except Exception as e:
            error(e)

    return {'status': 200, 'message': 'members added to group successfully', 'data': data}


# Bans a member from an existing group
# params -> chat_id(integer), user_id(integer)
async def ban_chat_member() -> dict:
    # Check if request method is POST
    if request.method != 'POST':
        return {'status': 405, 'message': 'method not allowed'}

    # Get data from request body
    data = request.json

    info(f'payload: {data}')

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id', 'user_id'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    # Ban members from group
    res, em = await telegram.ban_chat_member(data['chat_id'], data['user_id'])
    result = {'result': res, 'error': em}
    info(f'result: {result}')
    if not res:
        send_alert(f'{em}\n<b>Group id: </b>{data["chat_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later or contact PO'}

    return {'status': 200, 'message': 'member banned from group successfully', 'data': data}


# Send groups data to panel api
async def sync_groups() -> dict:
    # Return error if request method was not GET
    if request.method != 'GET':
        return {'status': 405, 'message': 'method not allowed'}

    # Get all groups
    groups = await telegram.get_all_groups()

    return {'status': 200, 'data': groups}


# Unarchive chat with given chat id
async def unarchive() -> dict:
    # Get data from request body
    data = request.json

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    is_unarchived, em = await telegram.unarchive(data['chat_id'])
    if not is_unarchived:
        send_alert(f'{em}\nGroup id: {data["chat_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later or contact PO'}

    # Get invite link for created group
    data['invite_link'] = await telegram.get_invite_link(data['chat_id'])

    return {'status': 200, 'message': 'chat unarchived successfully', 'data': data}


# Unban user from a group
async def unban_chat_member() -> dict:
    # Get data from request body
    data = request.json

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id', 'user_id'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    # Unban chat member with given data
    is_unbanned, em = await telegram.unban_chat_member(data['chat_id'], data['user_id'])
    if not is_unbanned:
        send_alert(f'{em}\n<b>Group id: </b>{data["chat_id"]}\n<b>User id: </b>{data["user_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later'}

    return {'status': 200, 'message': 'user unbanned successfully'}
