import os

import requests
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models.gigachat import GigaChat
from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemOut, ItemsOut, ItemUpdate, MessageInfo, Message, Chat, ChatOut, ChatCreate, CreateMessage, HistoryUpdate, Template
import logging
import functools
import datetime
import requests
import uuid
import base64
import http.client
import ssl


token = None
expired_datetime = 0
credentials = os.environ.get('SALUTE_SPEECH_CREDENTIALS')
cred_chat = os.environ.get('SBER_GIGACHAT_CREDENTIALS')


def get_token():
    try:
        # Create a unique RqUID using uuid
        rq_uid = str(uuid.uuid4())
        # Define headers and data payload
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {credentials}',
            'RqUID': rq_uid,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'scope': 'SALUTE_SPEECH_PERS'
        }

        # Combine headers and data in the request
        response = requests.post('https://ngw.devices.sberbank.ru:9443/api/v2/oauth', headers=headers, data=data,
                                 verify=False)
        if response.status_code != 200:
            logging.error("Error WHILE GETTING SBER TOKEN!")
        return response.json()
    except Exception as e:
        logging.error(f"Error while getting token! : {e.__str__()}")


def check_expired_token(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global token, expired_datetime
        if token is None:
            token_info = get_token()
            token = token_info["access_token"]
            expired_datetime = token_info["expires_at"] / 1000  # Convert milliseconds to seconds
        expires_at_seconds = expired_datetime / 1000  # Convert milliseconds to seconds

        if datetime.datetime.utcnow() < datetime.datetime.utcfromtimestamp(expires_at_seconds - 10):
            logging.error("Token is not expired, executing function...")
            return func(*args, **kwargs)
        else:
            logging.error("Token is expired, refreshing...")
            token_info = get_token()
            token = token_info["access_token"]
            expired_datetime = token_info["expires_at"] / 1000  # Convert milliseconds to seconds
            logging.error("Executing function after token refresh...")
            return func(*args, **kwargs)
    return wrapper


@check_expired_token
def send_to_gpt(session: SessionDep, chat_id) -> str:
    try:
        chat = session.get(Chat, chat_id)
        template = session.get(Template, chat.template_id)
        prompt = template.prompt
        message_history = chat.history["messages"]
        giga_chat = GigaChat(credentials=cred_chat, verify_ssl_certs=False, max_tokens=100)
        messages = [SystemMessage(content=prompt)]
        for message in message_history:
            if message["type"] == "human":
                messages.append(HumanMessage(content=message['content']))
            elif message["type"] == "ai":
                messages.append(AIMessage(content=message['content']))
        result = giga_chat(messages)
        return result.content
    except Exception as e:
        logging.error(f'Error while send message to gpt: {e.__str__()}')

@check_expired_token
def synthesize_text(text) -> str:
    try:
        context = ssl._create_unverified_context()

        conn = http.client.HTTPSConnection("smartspeech.sber.ru", context=context)
        payload = text
        headers = {
            'Content-Type': 'application/ssml',
            'Authorization': f'Bearer {token }'
        }
        conn.request("POST", "/rest/v1/text:synthesize?format=wav16&voice=Nec_8000", payload.encode('utf-8'), headers)
        res = conn.getresponse()
        response_content = res.read()
        path_file = f"app/assets/{str(uuid.uuid4())}_phrase.wav"
        logging.error(os.getcwd())
        with open(path_file, "wb") as f:
            f.write(response_content)
        return path_file
    except Exception as e:
        logging.error(f'Error while synthesizing text: {e.__str__()}')


@check_expired_token
def transcribe_audio(file_path) -> str:
    try:
        # API endpoint configuration
        api_url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
        headers = {'Authorization': f'Bearer {token }',
                   "Content-Type": "audio/x-pcm;bit=16;rate=16000"}
        payload = {
            'data': open(file_path, 'rb')
        }
        # Make the API request and print the response
        response = requests.post(api_url, headers=headers, data=payload['data'], verify=False)
        return response.json()['result'][0]
    except Exception as e:
        logging.error(f'Error while transcribing audio: {e.__str__()}')
