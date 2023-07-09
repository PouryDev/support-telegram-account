import os
import requests
from logging import error


# Checks if expected indexes are not null in a dictionary
def required(data: dict, expected: list):
    flag = True
    null_fields = []
    for key in expected:
        item = data.get(key)
        if item is None:
            flag = False
            null_fields.append(key)

    return flag, null_fields


# Send alert to monitoring group on exceptions
def send_alert(message: str):
    bot_token = os.getenv('MONITORING_BOT_TOKEN', '')
    monitoring_group_id = int(os.getenv('MONITORING_GROUP_ID'))
    related_usernames = os.getenv('MONITORING_RELATED_USERNAMES', '')

    try:
        requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', params={
            'chat_id': monitoring_group_id,
            'message': f'<b><i>#NOC_Telegram_Account</b></i>\n\n{message}\n\n<b><i>{related_usernames}</b></i>',
            'parse_mode': 'html',
        })
    except requests.exceptions.RequestException as e:
        error(e)
