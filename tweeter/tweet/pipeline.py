

def save_username_email(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        user.username = response.get('email').split('@')[0]  # part before @
        user.email = response.get('email')
        user.first_name = ''
        user.last_name = ''
        user.save()