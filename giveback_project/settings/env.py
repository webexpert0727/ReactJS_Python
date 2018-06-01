import ast
import os


def env(key, default=None):
    """
    Retrieves environment variables and returns Python natives. The (optional)
    default will be returned if the environment variable does not exist.
    """
    try:
        value = os.environ[key]
        if value.lower() in ['true', 'false']:
            value = value.title()
        elif value == '':
            raise KeyError()  # default value will be used instead of blank
        return ast.literal_eval(value)
    except (SyntaxError, ValueError, AttributeError):
        return value
    except KeyError:
        return default
