from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.core.celery_app import celery_app
from app.models import MessageInfo
from app.utils import send_test_email

router = APIRouter()


# @router.post(
#     "/test-celery/",
#     dependencies=[Depends(get_current_active_superuser)],
#     status_code=201,
# )
# def test_celery(body: MessageInfo) -> MessageInfo:
#     """
#     Test Celery worker.
#     """
#     celery_app.send_task("app.worker.test_celery", args=[body.message])
#     return MessageInfo(message="Word received")
#
#
# @router.post(
#     "/test-email/",
#     dependencies=[Depends(get_current_active_superuser)],
#     status_code=201,
# )
# def test_email(email_to: EmailStr) -> MessageInfo:
#     """
#     Test emails.
#     """
#     send_test_email(email_to=email_to)
#     return MessageInfo(message="Test email sent")
