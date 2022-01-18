"""Access to Octopus APi see """
from enum import Enum
import logging
import os
from typing import Any, Dict
import requests

from . import exceptions
from . import tool
from . import resource


class API():
    """Class for interacting with the Bitbucket resources"""
    logger = logging.getLogger(__name__)

    def __init__(
            self, bitbucket_workspace: str, username: str, password: str,
            bitbucket_url: str = 'https://api.bitbucket.org/2.0'):
        """Grants access to the Bitbucket API.

        Args:
            bitbucket_workspace (str): The Bitbucket workspace repositories reside under.
            username (str): The Bitbucket username used to access Bitbucket
            password (str): The password used to access Bitbucket.
            bitbucket_url (str, optional): Defaults to 'https://bitbucket.org/'.
        """
        self.bitbucket_workspace = bitbucket_workspace
        self.bitbucket_url = bitbucket_url

        self.session = requests.Session()
        self.session.auth = (username, password)

    def get_repositories(self, parameters: dict=None) -> tool.Pages:
        """Lists all of the repositories for a workspace.

        Args:
            parameters (dict, optional): Parameters used to query
                for repositories. Defaults to None.

        Returns:
            tool.Pages: Generator for Repository objects
        """
        url = '/'.join([
            self.bitbucket_url,
            'repositories',
            self.bitbucket_workspace])

        pages = tool.Pages(
            connection=tool.Connection(
                session=self.session,
                url_base=url),
            url=url,
            parameters=parameters,
            resource=resource.Repository)

        return pages

    def get_repository(self, repository_name: str, parameters: dict=None) -> resource.Repository:
        """Find a single repository in a workspace.

        Args:
            repository_name (str): [description]
            parameters (dict, optional): Parameters used to query for repository.
                Defaults to None.

        Returns:
            resource.Repository: Repository object representing the repository
                found within the workspace.
        """
        url = '/'.join([
            self.bitbucket_url,
            'repositories',
            self.bitbucket_workspace,
            repository_name])

        response = self.session.get(url, params=parameters)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise exceptions.ObjectDoesNotExist(*error.args, **error.__dict__) from error

        repository = resource.Repository(
            connection=tool.Connection(
                session=self.session,
                url_base=url),
            **response.json())

        return repository

    def get_pipelines(self, repository_name: str, parameters: dict=None) -> tool.Pages:
        """Lists all of the pipelines for a repository.

        Args:
            parameters (dict, optional): Parameters used to query for pipelines. Defaults to None.

        Returns:
            tool.Pages: Generator for Pipeline objects
        """
        url = '/'.join([
            self.bitbucket_url,
            'repositories',
            self.bitbucket_workspace,
            repository_name.lower(),
            'pipelines/'])

        pages = tool.Pages(
            connection=tool.Connection(
                session=self.session,
                url_base=url),
            url=url,
            parameters=parameters,
            resource=resource.Pipeline)

        return pages
