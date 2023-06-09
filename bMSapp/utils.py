
from django.shortcuts import redirect
from .models import Player, Coach, Manager, Profile
from django.contrib.auth.models import User, Group
from .models import *
from django.shortcuts import render, redirect
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import force_bytes


# this function helps creating notifications for the manager and is used in  views.py
def create_notification(owner, user, message):
    notification = Notification.objects.create(
        owner=owner, profile=user, message=message)
    notification.save()

# this function creates profile using user form and is used in views.py


def create_profile(request, user_form, profile_form):
    username = user_form.cleaned_data['username']
    password = user_form.cleaned_data['password1']
    first_name = user_form.cleaned_data['first_name']
    last_name = user_form.cleaned_data['last_name']
    role = profile_form.cleaned_data['role']
    phone_number = profile_form.cleaned_data['phone_number']
    date_of_birth = profile_form.cleaned_data['date_of_birth']
    email = user_form.cleaned_data['email']
    user = User.objects.create_user(
        username, password=password, first_name=first_name, last_name=last_name, email=email)
    profile = Profile.objects.create(
        user=user, phone_number=phone_number, date_of_birth=date_of_birth)

    user.is_active = False
    user.save()
    # sends activation email, after registering
    send_activation_email(request, user)
# adds based on role to groups
    if role == 'P':

        group = Group.objects.get_or_create(name='Players')[0]
        user.groups.add(group)
        player = Player(profile=profile)
        player.save()
        create_notification(player.profile, player.profile,
                            'has joined the team!')
    elif role == 'C':
        group = Group.objects.get_or_create(name='Coaches')[0]
        user.groups.add(group)

        coach = Coach(profile=profile)
        coach.save()
    elif role == 'M':
        group = Group.objects.get_or_create(name='Managers')[0]
        user.groups.add(group)

        manager = Manager(profile=profile)
        manager.save()
    return user

# redirects user to appropriate page based on group


def redirect_user(user):
    if user.groups.filter(name='Players').exists():
        return redirect('player_after_login')
    if user.groups.filter(name='Coaches').exists():
        return redirect('coach_after_login')
    if user.groups.filter(name='Managers').exists():
        return redirect('manager_after_login')

# these functions are used as decorators in views.py to limit access
# 1. only players can access


def is_player(user):
    return user.groups.filter(name='Players').exists()

# 2. only coaches can access


def is_coach(user):
    return user.groups.filter(name='Coaches').exists()

# 3. only managers can access


def is_manager(user):
    return user.groups.filter(name='Managers').exists()

# 4. only coaches and managers can access


def not_player(user):
    return not is_player(user)


# _______EMAIL_______
# EmailThread class extends threading.Thread and provides a custom implementation for sending emails
class EmailThread(threading.Thread):
    def __init__(self, subject, content, recipient_list, sender, Images=[], connection=settings.EMAIL_CONNECTIONS["proton"]):
        self.subject = subject
        self.recipient_list = recipient_list
        self.content = content
        self.sender = sender
        self.Images = Images
        self.connection = connection
        threading.Thread.__init__(self)
# called when thread starts

    def run(self):

        with get_connection(host=self.connection["host"], port=self.connection["port"], username=self.connection["username"], password=self.connection["password"], use_tls=self.connection["use_tls"], use_ssl=self.connection["use_ssl"]) as connect:
            msg = EmailMultiAlternatives(
                self.subject, self.content, self.sender, self.recipient_list, connection=connect)
            msg.send(fail_silently=False)


def send_mail(subject, content, recipient_list, sender, Images=[], connection=settings.EMAIL_CONNECTIONS["proton"]):
    EmailThread(subject, content, recipient_list, sender,
                Images=Images, connection=connection).start()

# AppTokenGenerator class extends PasswordResetTokenGenerator and provides a custom implementation for generating secure tokens


class AppTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return (text_type(user.is_active)+text_type(user.pk)+text_type(timestamp))


# Create an instance of AppTokenGenerator
token_generator = AppTokenGenerator()

# uses generated token and send_mail


def send_activation_email(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain
    # Generate activation URL with the encoded user ID and token
    link = reverse('activate', kwargs={
                   'uidb64': uidb64, 'token': token_generator.make_token(user)})
    activate_url = "http://"+domain+link
    email_subject = 'Activate your account'
    email_recipient = user.email
    email_body = 'Hi '+user.first_name + \
        "\nPlease use this link to verify your account\n"+activate_url
    # Call send_mail function to send the email with the activation link
    send_mail(email_subject, email_body, sender=settings.EMAIL_HOST_USER,
              recipient_list=[email_recipient])
