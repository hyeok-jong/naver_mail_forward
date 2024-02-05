import smtplib
import email
import imaplib
from email.header import decode_header
from tqdm import tqdm

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--password', type = str)
parser.add_argument('-t', '--to', type = str, default = 'jj770206@gmail.com')
parser.add_argument('-s', '--sender', type = str, default = 'jj770206@naver.com')
args = parser.parse_args()

# Email account credentials
email_to = args.to
email_from =  args.sender
email_from_password = args.password

# SMTP server information
SMTP_server_host = 'smtp.naver.com'
SMTP_port = 587

# IMAP server information
IMAP_server_host = 'imap.naver.com'
IMAP_port = 993



# Search for emails that are unread and within a specified date range
date_since = '01-Jan-2024'
# date_before = '10-Jan-2024'



# Connect to the IMAP server and select the inbox
client = imaplib.IMAP4_SSL(IMAP_server_host, IMAP_port)
client.login(email_from, email_from_password)
client.select('INBOX')

# Search for emails
# result, data = client.search(None, '(UNSEEN SINCE "{}" BEFORE "{}")'.format(date_since, date_before))
result, data = client.search(None, '(UNSEEN SINCE "{}")'.format(date_since))
email_ids = data[0].split()

for email_id in tqdm(email_ids):
    # Fetch the email
    result, email_data = client.fetch(email_id, "(RFC822)")
    
    if result == 'OK':
        print('start')
        email_body = email_data[0][1]
        message = email.message_from_bytes(email_body)
        
        # Decode subject and sender
        subject = message.get('Subject')
        decoded_subject = decode_header(subject)
        subject = ''.join([str(text, charset or 'utf-8') if charset else str(text) for text, charset in decoded_subject])
        sender = message.get('From')
        received_time = message.get('Date')  # Extracting the 'Date' header

        # Prepare additional info, handling '\n' replacement outside f-string
        additional_info_plain = f"Original Sender: {sender}\nReceived Time: {received_time}\n\n"
        additional_info_html = additional_info_plain.replace('\n', '<br>')
        
        # Append additional info to the email content
        if message.is_multipart():
            for part in message.get_payload():
                if part.get_content_type() == 'text/plain':
                    part.set_payload(additional_info_plain + part.get_payload())
                elif part.get_content_type() == 'text/html':
                    # Note the separation of HTML formatting from variable content
                    part.set_payload(f"<p>{additional_info_html}</p>" + part.get_payload())
        else:
            payload = message.get_payload(decode=True).decode()
            if message.get_content_type() == 'text/html':
                message.set_payload(f"<p>{additional_info_html}</p>" + payload)
            else:
                message.set_payload(additional_info_plain + payload)
        
        print("Subject:", subject, 'From:', sender, 'Received Time:', received_time)
        
        # Replace headers
        message.replace_header("From", email_from)
        message.replace_header("To", email_to)
        
        # SMTP server setup and send the email
        smtp = smtplib.SMTP(SMTP_server_host, SMTP_port)
        smtp.starttls()
        smtp.login(email_from, email_from_password)
        
        try:
            smtp.sendmail(email_from, email_to, message.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print("Failed to send email:", e)
        smtp.quit()
    else:
        print("Failed to fetch email.")

client.logout()