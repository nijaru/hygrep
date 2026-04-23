from celery import Celery
import os

app = Celery('myapp_tasks', broker=os.getenv('RABBITMQ_URL', 'amqp://guest@localhost//'))

@app.task
def send_async_email(email_address: str, subject: str):
    print(f"Sending email to {email_address} with subject: {subject}")\n