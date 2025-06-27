from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
import logging
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

DEFAULT_MODEL_NAME = "mariagrandury/roberta-base-finetuned-sms-spam-detection"


class SpamClassifier:
    """
    A wrapper for a Hugging Face sequence classification model to predict spam.
    Handles model loading, device placement, and inference.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        """
        Initializes the tokenizer and model.

        Args:
            model_name (str): The name of the pre-trained model from Hugging Face Hub.
        """
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logging.info(f"SpamClassifier using device: {self.device}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            logging.error(f"Failed to load model '{self.model_name}'. Error: {e}")
            raise

    def get_spam_probability(self, text: str) -> float:
        """
        Calculates the spam probability for a single piece of text.

        Args:
            text (str): The text to classify.

        Returns:
            float: The probability that the text is spam (a value between 0.0 and 1.0).
        """
        return self.get_spam_probabilities_batch([text])[0]

    def get_spam_probabilities_batch(self, texts: List[str]) -> List[float]:
        """
        Calculates spam probabilities for a batch of texts. This is more efficient
        for processing multiple emails at once.

        Args:
            texts (List[str]): A list of texts to classify.

        Returns:
            List[float]: A list of spam probabilities corresponding to each input text.
        """
        try:
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            spam_probabilities = predictions[:, 1].tolist()
            return spam_probabilities
        except Exception as e:
            logging.error(f"Error during batch classification: {e}")
            return [0.0] * len(texts)


if __name__ == "__main__":
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    print("--- Running SpamClassifier Tests ---")
    try:
        spam_classifier = SpamClassifier()

        test_emails = [
            "Congratulations! You've won a free ticket. Click here to claim.",
            "Did you get that email from John?.",
            "This is a copy of a security alert sent to john@gmail.com. johnjohn@gmail.com is the recovery email for this account. If you don't recognise this account, remove it.",
            "URGENT: Your account has been compromised! Verify your identity now!",
        ]

        print("\n--- Testing Batch Classification ---")
        probabilities = spam_classifier.get_spam_probabilities_batch(test_emails)
        for email, prob in zip(test_emails, probabilities):
            status = "SPAM" if prob > 0.95 else "NOT SPAM"
            print(f"Probability: {prob:.2%} [{status}] - Text: \"{email[:50]}...\"")

        print("\n--- Testing Single Classification ---")
        single_test = "Hey, are we still on for lunch tomorrow?"
        prob = spam_classifier.get_spam_probability(single_test)
        status = "SPAM" if prob > 0.95 else "NOT SPAM"
        print(f"Probability: {prob:.2%} [{status}] - Text: \"{single_test[:50]}...\"")

    except Exception as e:
        print(f"\n--- Test Failed ---")
        print(f"An error occurred during initialization or testing: {e}")
