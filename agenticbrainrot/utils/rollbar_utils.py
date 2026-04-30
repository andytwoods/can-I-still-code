import hashlib

def transform_rollbar_payload(payload, **kwargs):
    """
    Custom transform function for Rollbar to improve grouping.
    It can be used to set a custom fingerprint for certain types of errors
    to prevent 'lots and lots of errors of the same thing'.
    """
    # Example: Group all ConnectionErrors together regardless of the message
    # if you find they are cluttering your dashboard.

    # Extract the exception data if available
    body = payload.get('body', {})
    trace = body.get('trace')

    if trace:
        exception = trace.get('exception', {})
        exc_class = exception.get('class')

        # If it's a specific noisy exception, we can force a fingerprint
        # to ensure they are all grouped into one item.
        if exc_class in ['ConnectionError', 'BrokenPipeError']:
            payload['fingerprint'] = hashlib.md5(exc_class.encode('utf-8')).hexdigest()

    return payload
