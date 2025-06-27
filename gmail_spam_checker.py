from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import os
import logging
from spam_classifier import SpamClassifier

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
PROCESSED_LABEL_NAME = 'ML_PROCESSED'
POLL_INTERVAL_SECONDS = 60
SPAM_CONFIDENCE_THRESHOLD = 0.95
TRUSTED_DOMAINS = [
    '@google.com', '@gmail.com', '@github.com', '@microsoft.com', '@amazon.com'
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def get_credentials() -> Credentials | None:
    """Handles user authentication and token management."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Failed to refresh token: {e}")
                creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def ensure_processed_label(service) -> str | None:
    """Checks if the 'processed' label exists and creates it if not."""
    try:
        labels_response = service.users().labels().list(userId='me').execute()
        for label in labels_response.get('labels', []):
            if label['name'] == PROCESSED_LABEL_NAME:
                logging.info(f"Found existing label: '{PROCESSED_LABEL_NAME}'")
                return label['id']

        logging.info(f"Creating label: '{PROCESSED_LABEL_NAME}'")
        label_body = {
            'name': PROCESSED_LABEL_NAME,
            'labelListVisibility': 'labelHide',
            'messageListVisibility': 'hide'
        }
        created_label = service.users().labels().create(userId='me', body=label_body).execute()
        return created_label['id']
    except HttpError as e:
        logging.error(f"Failed to ensure label exists: {e}")
        return None


def modify_message_labels(service, msg_id: str, labels_to_add: list, labels_to_remove: list):
    """A generic function to modify labels for a given message."""
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': labels_to_add, 'removeLabelIds': labels_to_remove}
        ).execute()
    except HttpError as e:
        logging.error(f"Failed to modify labels for message {msg_id}: {e}")


def poll_gmail(classifier: SpamClassifier):
    """Main loop to poll Gmail, classify emails, and take action."""
    creds = get_credentials()
    if not creds:
        logging.error("Could not obtain credentials. Exiting.")
        return

    service = build('gmail', 'v1', credentials=creds)
    processed_label_id = ensure_processed_label(service)
    if not processed_label_id:
        logging.error("Could not obtain or create a processing label. Exiting.")
        return

    while True:
        try:
            query = f'is:unread -label:{PROCESSED_LABEL_NAME}'
            response = service.users().messages().list(userId='me', q=query).execute()
            messages = response.get('messages', [])

            if not messages:
                logging.info("No new unread messages. Waiting...")
            else:
                logging.info(f"Found {len(messages)} new message(s) to process.")

            for msg in messages:
                email = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()

                headers = {h['name']: h['value'] for h in email['payload']['headers']}
                subject = headers.get('Subject', '[No Subject]')
                sender = headers.get('From', '[No Sender]')
                snippet = email['snippet']

                if any(domain in sender.lower() for domain in TRUSTED_DOMAINS):
                    logging.info(f"TRUSTED: '{subject}' from {sender}")
                    modify_message_labels(service, email['id'], [processed_label_id], [])
                    continue

                text_to_classify = f"Subject: {subject} From: {sender} Body: {snippet}"
                spam_probability = classifier.get_spam_probability(text_to_classify)

                if spam_probability > SPAM_CONFIDENCE_THRESHOLD:
                    logging.warning(f"SPAM ({spam_probability:.2%}): '{subject}'")
                    modify_message_labels(service, email['id'], ['SPAM'], ['INBOX'])
                else:
                    logging.info(f"NOT SPAM ({spam_probability:.2%}): '{subject}'")
                    modify_message_labels(service, email['id'], [processed_label_id], [])

        except HttpError as e:
            logging.error(f"An API error occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    spam_classifier = SpamClassifier()
    poll_gmail(spam_classifier)