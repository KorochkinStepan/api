import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemOut, ItemsOut, ItemUpdate, MessageInfo, TemplateOut, TemplateCreate, Template, TemplatesOut

router = APIRouter()


@router.post("/", response_model=TemplateOut)
def create_template(session: SessionDep, current_user: CurrentUser, template_in: TemplateCreate) -> Any:
    """
    Create chat
    :param session:
    :param current_user:
    :param template_in:
    :return:
    """
    chat = Template.model_validate(template_in, update={"owner_id": current_user.id})
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


@router.delete("/{chat_id}")
def delete_template(session: SessionDep, current_user: CurrentUser, template_id: int) -> Any:
    """
    :param session:
    :param current_user:
    :param template_id:
    :return:
    """
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not ((template.owner_id == current_user) or current_user.is_superuser):
        return HTTPException(status_code=400, detail="You are not superuser or owner of Template")
    session.delete(template)
    session.commit()
    return MessageInfo(message="Template deleted successfully")


@router.get("/templates", response_model=TemplatesOut)
def get_all_templates(session: SessionDep, current_user: CurrentUser) -> Any:
    try:
        statement = select(Template).where(or_(Template.owner_id == current_user.id, Template.private == False))
        templates = session.exec(statement).all()
        return TemplatesOut(templates=templates, count=len(templates))
    except Exception as e:
        logging.error(f"Error! {e.__str__()}")
        raise HTTPException(status_code=400, detail="You are not superuser or owner of chat")