import hashlib

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import transaction
from django.template.defaultfilters import slugify

import facebook
from facebook.models import User as FacebookUser


@transaction.commit_on_success
def get_or_create_user(username, defaults):
    """
    Hopefully a bit safer version of User.objects.get_or_create

    Thanks, StackOverflow:

    http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django
    """
    try:
        user = User.objects.create(username=username, **defaults)
    except IntegrityError: # Probably a duplicate?
        transaction.commit()
        user = User.objects.get(username=username)
    return user


class AuthenticationBackend(object):
    supports_anonymous_user = False

    def authenticate(self, uid=None, access_token=None):
        if not uid:
            raise AttributeError, 'FB Authentication Backend got no user id.'

        try:
            graph = facebook.GraphAPI(access_token)
            profile = graph.get_object("me")
        except (facebook.GraphAPIError, IOError): # IOError because of timeouts
            return None

        try:
            facebook_user = FacebookUser.objects.get(id=uid)
            facebook_user.access_token = access_token
            facebook_user.save_from_facebook(profile)
            user = facebook_user.user
        except ObjectDoesNotExist:
            # The Facebook user instance might already exist in the database.
            # Fetch the record using the Facebook ``uid`` -- this should prevent
            # integrity errors from the database in the future.
            try:
                facebook_user = FacebookUser.objects.get(id=uid)
            except FacebookUser.DoesNotExist:
                facebook_user = FacebookUser(id=uid, access_token=access_token)

            user = get_or_create_user(slugify(profile['id']), {
                    'email': profile.get('email', u''),
                    'first_name': profile.get('first_name', u''),
                    'last_name': profile.get('last_name', u''),
                    'password': hashlib.md5(uid).hexdigest(),
                    })

            facebook_user.user = user
            facebook_user.save_from_facebook(profile)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None