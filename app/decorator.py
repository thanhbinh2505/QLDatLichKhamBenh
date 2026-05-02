from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, abort


def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login_process'))

            roles_list = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]

            if current_user.role not in roles_list:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator