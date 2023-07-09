from flask import Flask
import telegram
from controllers import groups, message
from middlewares.auth import AuthMiddleware
from logging.config import dictConfig


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

# Create flask instance
app = Flask(__name__)

# Call auth middleware to check service key
app.wsgi_app = AuthMiddleware(app.wsgi_app)


# Define routes

# Create telegram group with given title and description
@app.route('/group/create', methods=['POST'])
async def create_group():
    return await groups.create()


# Delete an existing group with given chat_id
@app.route('/group/delete', methods=['POST'])
async def delete_group():
    return await groups.archive()


# Unarchive an existing group with given chat_id
@app.route('/group/unarchive', methods=['POST'])
async def uanrchive_group():
    return await groups.unarchive()


# Add members to an existing group
@app.route('/group/members/add', methods=['POST'])
async def add_chat_members():
    return await groups.add_chat_members()


# Ban members from an existing group
@app.route('/group/members/ban', methods=['POST'])
async def ban_chat_member():
    return await groups.ban_chat_member()


@app.route('/groups', methods=['GET'])
async def sync_groups():
    return await groups.sync_groups()


@app.route('/message/delete', methods=['POST'])
async def delete_message():
    return await message.delete()


@app.route('/message/edit', methods=['POST'])
async def edit_message():
    return await message.edit()


@app.route('/message/send', methods=['POST'])
async def send_message():
    return await message.send()


@app.route('/contacts/sync', methods=['GET'])
async def sync_contacts():
    return await telegram.get_contacts()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

