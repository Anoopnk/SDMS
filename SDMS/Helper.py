import datetime


def nowUTC():
    """
    Get the current time in UTC.
    :return:
    """
    return datetime.datetime.now(datetime.timezone.utc)
