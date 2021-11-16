import requests

class ObjectDoesNotExist(IOError):
    """Class for indicating a Bitbucket resource requested does not exist"""
    def __init__(self, *args, **kwargs):
        """Initialize RequestException with `request` and `response` objects."""
        response = kwargs.pop('response', None)
        self.response = response
        self.request = kwargs.pop('request', None)
        if (response is not None and not self.request and
                hasattr(response, 'request')):
            self.request = self.response.request

        super(ObjectDoesNotExist, self).__init__(*args, **kwargs)
