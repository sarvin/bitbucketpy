"""Generate an iterator for "paging" through list calls"""
from collections import namedtuple
from typing import NamedTuple
import logging
import requests


# Connection = namedtuple('Connection', 'session, url_base')

class Connection(NamedTuple):
    session: requests.sessions.Session
    url_base: str


class Pages():
    """Class for paging over data"""
    logger = logging.getLogger(__name__)

    def __init__(self, connection: Connection, url: str, resource, parameters: dict=None):
        """Create an iterator for URLs that hand back multiple resources that span
        multiple requests

        Args:
            connection (Connection):
            url (str): URL we use to query for the first page.
                API then tells us what the next page should be.
            resource (octopus.resource.*): The Class we'll use to generate objects.
            parameters (dict): dictionary of data to be used as URL parameters when
                making a get request.
        """
        self.connection = connection
        self.url_next = url
        self.api_class = resource
        self.parameters = parameters
        self.index = -1
        self.json = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            self.index += 1

            try:
                json_resource = self.json['values'][self.index]
            except (IndexError, TypeError):
                if self.url_next:
                    self.get_page()
                else:
                    raise StopIteration
            else:
                api_resource = self.api_class(
                    connection=self.connection,
                    **json_resource)

                return api_resource

    def get_page(self):
        self.logger.debug("url_next=%s with parameters=%s", self.url_next, self.parameters)

        response = self.connection.session.get(self.url_next, params=self.parameters)
        response.raise_for_status()

        self.json = response.json()

        ### Let Octopus decide our URL parameters
        ### after the initial request
        self.parameters = None

        if self.json.get('next'):
            self.url_next = self.json.get('next')
        else:
            self.url_next = None

        self.index = -1
