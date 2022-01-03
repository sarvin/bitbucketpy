"""Test suite for the bitbucket.tool module"""
import random
import string
import unittest
from unittest.mock import Mock

import src.bitbucket


class Page(unittest.TestCase):
    """Test cases for the bitbucket.tool.Pages class"""

    def test_get_page(self):
        """When multiple pages exist query all pages till "next" is None"""
        # Arrange
        session = Mock()
        connection = src.bitbucket.tool.Connection(
            session=session,
            url_base='https://api.bitbucket.org/2.0/repositories/test_workspace/test_repository')

        response_1 = Mock(status_code=200)
        response_1.json.return_value = {
            'next': f'{connection.url_base}/refs/branches?page=2',
            'page': 1,
            'pagelen': 10,
            'size': 29,
            'values': [
                {'name': f'{x}{"".join(random.choices(string.ascii_lowercase + string.digits, k=4))}'} # pylint: disable=line-too-long
                for x in range(1,11)]}

        response_2 = Mock(status_code=200)
        response_2.json.return_value = {
            'next': f'{connection.url_base}/refs/branches?page=3',
            'page': 2,
            'pagelen': 10,
            'previous': f'{connection.url_base}/refs/branches?page=1',
            'size': 29,
            'values': [
                {'name': f'{x}{"".join(random.choices(string.ascii_lowercase + string.digits, k=4))}'} # pylint: disable=line-too-long
                for x in range(11,21)]}

        response_3 = Mock(status_code=200)
        response_3.json.return_value = {
            'page': 3,
            'pagelen': 9,
            'previous': f'{connection.url_base}/refs/branches?page=2',
            'size': 29,
            'values': [
                {'name': f'{x}{"".join(random.choices(string.ascii_lowercase + string.digits, k=4))}'} # pylint: disable=line-too-long
                for x in range(21,30)]}


        session.get.side_effect = [
            response_1,
            response_2,
            response_3,
        ]

        pages = src.bitbucket.tool.Pages(
            connection=connection,
            url=f'{connection.url_base}/refs/branches',
            resource=src.bitbucket.resource.Branch)

        # Act
        resources = list(pages)

        # Assert
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(len(resources), 29)

    def test_get_page_single_resource(self):
        """When a single resource exists for query (size of 1)
        then only one resource should be returned
        """
        # Arrange
        commit_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=39))

        session = Mock()
        connection = src.bitbucket.tool.Connection(
            session=session,
            url_base='https://api.bitbucket.org/2.0/repositories/test_workspace/test_repository')

        response_1 = Mock()
        response_1.status_code = 200
        response_1.json.return_value = {
            'pagelen': 10,
            'values': [
                {
                    'key': '-897687013',
                    'description': '',
                    'repository': {},
                    'url': f'{connection.url_base}/addon/pipelines/home#!/results/65027',
                    'links': {},
                    'refname': 'test_ref_name',
                    'state': 'SUCCESSFUL',
                    'created_on': '2021-12-28T12:14:51.294037+00:00',
                    'commit': {},}],
            'page': 1,
            'size': 1}

        session.get.side_effect = [
            response_1,
        ]

        pages = src.bitbucket.tool.Pages(
            connection=connection,
            url=f'{connection.url_base}/commit/{commit_string}/statuses',
            resource=src.bitbucket.resource.Build)

        # Act
        resources = list(pages)

        # Assert
        self.assertEqual(session.get.call_count, 1)
        self.assertEqual(len(resources), 1)

    def test_get_page_missing_next_in_response(self):
        """When the "next" parameter is missing from the
        return value make next queries based on total count
        """
        # Arrange
        session = Mock()
        connection = src.bitbucket.tool.Connection(
            session=session,
            url_base='https://api.bitbucket.org/2.0/repositories/test_workspace/test_repository')

        response_1 = Mock()
        response_1.status_code = 200
        response_1.json.return_value = {
            'page': 1,
            'pagelen': 10,
            'size': 20,
            'values': [{'build_number': 65027},
                {'build_number': 64678},
                {'build_number': 64507},
                {'build_number': 64334},
                {'build_number': 64141},
                {'build_number': 63777},
                {'build_number': 63758},
                {'build_number': 63756},
                {'build_number': 63755},
                {'build_number': 63750}]}

        response_2 = Mock()
        response_2.json.return_value = {'page': 2,
            'pagelen': 10,
            'size': 20,
            'values': [
                {'build_number': 63749},
                {'build_number': 63748},
                {'build_number': 63747},
                {'build_number': 63746},
                {'build_number': 63745},
                {'build_number': 63734},
                {'build_number': 63707},
                {'build_number': 63577},
                {'build_number': 63576},
                {'build_number': 63575}]}

        session.get.side_effect = [
            response_1,
            response_2]

        pages = src.bitbucket.tool.Pages(
            connection=connection,
            url=f'https://{connection.url_base}/pipelines/',
            parameters={
                'target.branch':'INVECL-49154',
                'sort': '-created_on'},
            resource=src.bitbucket.resource.Pipeline)

        # Act
        resources = list(pages)

        # Assert
        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(len(resources), 20)
