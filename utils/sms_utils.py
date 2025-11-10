def send_sms_alert(to_number, message):
    """
    Sends an SMS alert to the specified number.
    This is a placeholder function — replace with real SMS gateway logic.

    Parameters:
    - to_number (str): Recipient's phone number (e.g., +254712345678)
    - message (str): Message content
    """
    print(f"[SMS] To: {to_number} | Message: {message}")
    # TODO: Integrate with Africa's Talking, Twilio, or another SMS provider
