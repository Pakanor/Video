from django.core.mail import send_mail
send_mail(
    "Subject here",
    "Here is the message.",
    "robert.p3@o2.pl",
    ["parchatkarobert@gmail.com"],
    fail_silently=False,
)
