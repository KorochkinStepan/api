import copy
import logging
import uuid
from typing import Any, Optional, Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import func, select, delete
from psycopg2.extras import Json
from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemOut, ItemsOut, ItemUpdate, MessageInfo, Message, Chat, ChatOut, ChatCreate, CreateMessage, HistoryUpdate
from app.api.sber_backend import send_to_gpt, synthesize_text, transcribe_audio


router = APIRouter()


@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(session: SessionDep, current_user: CurrentUser, chat_id: int) -> Any:
    """
    Get chat by ID.
    """
    try:
        chat = session.get(Chat, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Item not found")
        if not current_user.is_superuser and (chat.owner_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")
    except Exception as e:
        logging.error(f"Error! : {e.__str__()}")
    return chat


@router.post("/", response_model=ChatOut)
def create_chat(session: SessionDep, current_user: CurrentUser, chat_in: ChatCreate) -> Any:
    """
    Create chat
    :param session:
    :param current_user:
    :param chat_in:
    :return:
    """
    try:
        chat = Chat.model_validate(chat_in, update={"owner_id": current_user.id})
        session.add(chat)
        session.commit()
        session.refresh(chat)
    except Exception as e:
        logging.error(f"Error! : {e.__str__()}")
    return chat


@router.delete("/{chat_id}")
def delete_chat(session: SessionDep, current_user: CurrentUser, chat_id: int) -> Any:
    """
    :param session:
    :param current_user:
    :param chat_id:
    :return:
    """
    try:
        chat = session.get(Chat, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="chat not found")
        if not ((chat.owner_id == current_user) or current_user.is_superuser):
            return HTTPException(status_code=400, detail="You are not superuser or owner of chat")
        statement = delete(Message).where(Message.chat_id == chat_id)
        session.exec(statement)
        session.delete(chat)
        session.commit()
    except Exception as e:
        logging.error(f"Error! : {e.__str__()}")
    return MessageInfo(message="chat deleted successfully")


@router.post("/pass_message", response_model=ChatOut)
def pass_message(session: SessionDep, current_user: CurrentUser,
                 chat_id: int,
                 file: UploadFile,
                 text: str | None = None,
                 ) -> Any:
    """

    :param chat_id:
    :param file:
    :param text:
    :param session:
    :param current_user:
    :return:
    """
    try:
        chat = session.get(Chat, chat_id)
        if chat.owner_id != current_user.id:
            return MessageInfo(message="You can't access to this chat. User id is wrong")

        if text is None and file is None:
            return MessageInfo(message="You need to provide text or file at least")
        if text:
            logging.error(f'TEXT IS {text}')
            message_in = CreateMessage(chat_id=chat_id, body=text)
        else:
            path_file = f"app/assets/{str(uuid.uuid4())}_phrase.wav"
            with open(path_file, "wb") as f:
                f.write(file.file.read())
            text = transcribe_audio(path_file)
            message_in = CreateMessage(chat_id=chat_id, body=text)
        message = Message.model_validate(message_in)
        chat.messages.append(message)

        hist = copy.deepcopy(chat.history)
        if file:
            hist["messages"].append({"type": "human", "content": message_in.body, "path_file": path_file})
        else:
            hist["messages"].append({"type": "human", "content": message_in.body})
        history = HistoryUpdate(history=hist)
        history_data = history.model_dump(exclude_unset=True)
        chat.sqlmodel_update(history_data)
        session.add(message)
        session.add(chat)
        session.commit()
        session.refresh(message)
        session.refresh(chat)

        # create SBER message
        ai_message_str = send_to_gpt(session=session, chat_id=chat.id)
        ai_message = CreateMessage(chat_id=chat.id, body=ai_message_str)
        ai_message = Message.model_validate(ai_message)
        chat.messages.append(ai_message)
        hist = copy.deepcopy(chat.history)
        file = synthesize_text(ai_message_str)
        hist["messages"].append({"type": "ai", "content": ai_message.body, "path_file": file})
        history = HistoryUpdate(history=hist)
        history_data = history.model_dump(exclude_unset=True)
        chat.sqlmodel_update(history_data)
        session.add(chat)
        session.commit()
        session.refresh(chat)
    except Exception as e:
        logging.error(f"Error! : {e.__str__()}")
    return chat
