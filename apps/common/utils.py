import os

from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


import uuid

def serialize_tree(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "node_id": uuid.uuid4(),
        "name": node.name,
        "description": node.description,
        "video_link": node.video_link,
        "video_name": node.video_name,
        "video_duration": node.video_duration,
        "has_saved": True,
        "children": [serialize_tree(child) for child in node.get_children()],
    }

def send_sendgrid_email(to_emails, subject, content):
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
            html_content=content,
        )

        if not settings.DEBUG:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            sg.send(message)
        else:
            print("Email sent:", flush=True)
            print(message, flush=True)
    except Exception as e:
        print("Send Grid Email Failed:", e, flush=True)
