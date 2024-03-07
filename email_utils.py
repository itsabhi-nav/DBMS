import smtplib
from email.message import EmailMessage

def sendEmail(to, sub, msg, GMAIL_ID, GMAIL_PSWD):
    print(f"Email to {to} sent with subject: {sub} and message: {msg}")
    em = EmailMessage()
    em['From'] = GMAIL_ID
    em['To'] = to
    em['Subject'] = sub
    em.set_content(msg)

    context = smtplib.SMTP('smtp.gmail.com', 587)
    context.starttls()
    context.login(GMAIL_ID, GMAIL_PSWD)
    context.sendmail(GMAIL_ID, to, em.as_string())
    context.quit()
