from logging import error
from flask import request
import helpers
import telegram
from helpers import send_alert
from pyrogram.enums import ParseMode


# Edit message with given chat and message id
async def edit() -> dict:
    # Get data from request body
    data = request.json

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id', 'message_id', 'message'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    # Edit message with given data and return error on failure
    res, em = await telegram.edit_message(data['message_id'], data['chat_id'], data['message'])
    if not res:
        send_alert(f'{em}\n<b>Group id: </b>{data["chat_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later'}

    return {'status': 200, 'message': 'message edited successfully'}


# Delete message with given chat and message id
async def delete() -> dict:
    # Get data from request body
    data = request.json

    # Check if required values are filled
    validated, null_fields = helpers.required(data, ['chat_id', 'message_id'])
    if not validated:
        return {'status': 422, 'message': 'please all fields', 'data': null_fields}

    # Delete message and return error on failure
    res, em = await telegram.delete_message(data['message_id'], data['chat_id'])
    if not res:
        send_alert(f'{em}\n<b>Group id: </b>{data["chat_id"]}')
        return {'status': 500, 'message': 'something went wrong please try again later'}

    return {'status': 200, 'message': 'message deleted successfully'}


# Send message with given text to chat ids
async def send() -> dict:
    # Get data from request body
    data = request.json

    # Validate data and return error on failure
    validated, null_fields = helpers.required(data, ['chat_ids', 'message'])
    if not validated:
        return {'status': 422, 'message': 'please fill all fields', 'data': null_fields}

    # Get client instance
    app = await telegram.get_client()

    # init skipped groups and messages lists
    skipped_groups = []
    messages = []

    # make sure chat_ids is list
    if type(data['chat_ids']) != list:
        data['chat_ids'] = [data['chat_ids']]

    # get chat id from data
    chat_id = data['chat_ids'][0]

    try:
        # send message to target chat(group)
        message = await app.send_message(chat_id, data['message'], parse_mode=ParseMode.MARKDOWN)
        # pin group if pin has been sent in payload
        if 'pin' in data and data['pin']:
            await message.pin(disable_notification=False)
        # add message id and chat id of message to return in response
        messages.append({'message_id': message.id, 'chat_id': message.chat.id})
    except Exception as e:
        error(e)
        # add skipped group chat id which failed to message to it
        skipped_groups.append(chat_id)

    # stop client
    await app.stop()

    return {
        'status': 200,
        'message': 'message sent successfully',
        'data': {
            'skipped_groups': skipped_groups,
            'message': messages,
        }
    }

