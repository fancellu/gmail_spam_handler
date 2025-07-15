# Gmail Spam Checker

An automated Gmail spam detection system using machine learning. This script monitors your inbox, classifies new emails as spam or not spam, and automatically moves detected spam to the spam folder while leaving legitimate emails unread for your review.

## Features

-   **Automatic spam detection** using a pre-trained transformer model from Hugging Face.
-   **Smart processing** that only checks unread emails and marks them to prevent re-processing.
-   **Non-destructive** workflow that keeps legitimate emails unread in your inbox.
-   **Trusted Senders** list to automatically bypass checks for known-good domains.
-   **Custom labeling** to keep track of emails that have already been analyzed.

## Files

-   `gmail_spam_checker.py` - The main script that polls Gmail and orchestrates the process.
-   `spam_classifier.py` - A wrapper for the machine learning model that handles spam classification.
-   `requirements.txt` - A list of all the required Python dependencies.
-   `README.md` - This documentation file.

## Tutorial

[Tutorial](tutorial/index.md

## Setup

### 1. Install Dependencies

Ensure you have Python 3.8+ installed. Then, install the required packages using pip:

```bash
pip install -r requirements.txt
```

### 2. Create Google Cloud Credentials

**You must create your own `credentials.json` file:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file
   - Rename it to `credentials.json` and place in this directory

### 3. First Run Authentication

On first run, the script will:
1. Open your browser for Google OAuth
2. Ask you to sign in and grant permissions
3. Create a `token.json` file for future use

### 4. Run the Spam Checker

```bash
python gmail_spam_checker.py
```

## How It Works

1. **Polls Gmail** every 60 seconds for unread emails
2. **Extracts content** (subject, sender, body snippet)
3. **Classifies spam** using ML model (threshold: 90% confidence)
4. **Actions taken**:
   - **Spam detected**: Moves to spam folder
   - **Not spam**: Adds hidden label to avoid re-processing
5. **Leaves legitimate emails unread** in your inbox

## Customization

You can easily customize the script's behavior by modifying the configuration constants at the top of gmail_spam_checker.py:

| Constant                    | Default Value    | Description | 
|--------------------------|  -------------------------- | --------------- | 
|POLL_INTERVAL_SECONDS     | 60             | How often (in seconds) to check for new mail.                                      | 
|SPAM_CONFIDENCE_THRESHOLD | 0.95           | The probability score required to mark an email as spam (e.g., 0.95 = 95%).        | 
|TRUSTED_DOMAINS           | [...]          | A list of sender domains to automatically trust and skip processing.               | 
|PROCESSED_LABEL_NAME      | 'ML_PROCESSED' | The name of the label used to mark emails that have already been checked.          |

## Security Notes

- **Never commit** `credentials.json` or `token.json` to version control
- These files contain sensitive authentication data
- Each user must create their own credentials
- The app only requests Gmail modify permissions (no read access to other Google services)

## Troubleshooting

- **Authentication issues**:  If you encounter persistent authentication errors, delete the token.json file and run the script again to re-authenticate.
- **API quota exceeded**: The Gmail API has usage limits. If you see quota errors, you may need to increase the POLL_INTERVAL_SECONDS in the configuration to reduce the number of requests.

)