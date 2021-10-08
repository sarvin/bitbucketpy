"""Classes representing Bitbucket resources"""
from enum import Enum
from types import SimpleNamespace
from typing import Union
import copy
import time

from  . import tool

@property
def branches_from_link(self) -> tool.Pages:
    pages = tool.Pages(
        connection=self.connection,
        url=self.links['branches']['href'],
        resource=Branch)

    return pages

@property
def commits_from_link(self) -> tool.Pages:
    pages = tool.Pages(
        connection=self.connection,
        url=self.links['commits']['href'],
        resource=Commit)

    return pages

@property
def pullrequests_from_link(self) -> tool.Pages:
    pages = tool.Pages(
        connection=self.connection,
        url=self.links['pullrequests']['href'],
        resource=Tag)

    return pages

@property
def tags_from_link(self) -> tool.Pages:
    pages = tool.Pages(
        connection=self.connection,
        url=self.links['tags']['href'],
        resource=Tag)

    return pages

def get_branch(self, branch_name) -> "Branch":
    url = '/'.join([
        self.links['branches']['href'],
        branch_name])

    response = self.connection.session.get(url)
    response.raise_for_status()

    branch = Branch(
        connection=self.connection,
        **response.json())

    return branch


class Base(SimpleNamespace):
    def __init__(self, connection: tool.Connection, **kwargs) -> None:
        super().__init__(**kwargs)

        self.connection = connection

    def refresh(self):
        url = self.links['self']['href']

        response = self.connection.session.get(url)
        response.raise_for_status()

        self.__dict__.update(**response.json())


class Branch(Base):
    """Helper class for Branches"""

    commits = commits_from_link


class Commit(Base):
    """Helper class for Commits"""


class Pullrequest(Base):
    """Helper class for Pullrequests"""

    commits = commits_from_link
    def merge(self, merge_strategy: "PullrequestMergeStrategy", message: str) -> Union["Pullrequest", "PullrequestWaiter"]:
        url = self.links['merge']['href']

        data = {
            'type': 'pullrequest',
            'message': message,
        }

        if merge_strategy.value:
            data['merge_strategy'] = merge_strategy.value

        response = self.connection.session.post(url, json=data)
        response.raise_for_status()

        return_value = None
        if response.headers.get('Location'):
            return_value = PullrequestWaiter(self.connection, response.headers.get('Location'))
        else:
            return_value = Pullrequest(
                connection=self.connection,
                **response.json())

        return return_value

    @property
    def merge_commit_object(self) -> Commit:
        """Commit object representing the merging of two histories done
        through a pullrequest.

        Returns:
            Commit: object representing the merging of two histories
        """
        url = self.merge_commit['links']['self']['href']
        response = self.connection.session.get(url)

        commit = Commit(
            connection=self.connection,
            **response.json())

        return commit


class PullrequestWaiter():
    def __init__(self, connection: tool.Connection, location: str):
        self.connection = connection
        self.location = location

    def ready(self):
        status = False

        poll_merge = self.connection.session.get(
            self.location)
        poll_merge.raise_for_status()

        if poll_merge.status_code == 400:
            status = True

        if poll_merge.json().get('task_status') == 'SUCCESS':
            status = True

        return status

    def response(self):
        poll_merge = self.connection.session.get(
            self.location)

        return poll_merge

    def wait(self, delay: int, max_attempts: 40):
        for x in range(0, max_attempts):
            time.sleep(delay)

            poll_merge = self.connection.session.get(self.location)

            if poll_merge.json().get('task_status') == 'PENDING':
                continue

            if poll_merge.status_code == 400:
                break

            if poll_merge.json().get('task_status') == 'SUCCESS':
                break


class Repository(Base):
    """Helper class for Repositories"""

    branch = get_branch
    branches = branches_from_link
    pullrequests = pullrequests_from_link
    tags = tags_from_link

    def pullrequest(self, pullrequest_id: int) -> "Pullrequest":
        """Method for retrieving a existing pullrequest from Bitbucket

        Args:
            pullrequest_id (int): The ID of the pullrequest

        Returns:
            Pullrequest: object representing a pullrequest
        """
        url = '/'.join([
            self.links['pullrequests']['href'],
            str(pullrequest_id)])

        response = self.connection.session.get(url)
        response.raise_for_status()

        pullrequest = Pullrequest(
            connection=self.connection,
            **response.json())

        return pullrequest

    def create_pullrequest(self, pullrequest_data: "PullrequestData") -> "Pullrequest":
        """Method for creating a pullrequest in Bitbucket

        Args:
            pullrequest_data (PullrequestData): object instantiated with data
                required to create a pullrequest.

        Returns:
            Pullrequest: object representing a pullrequest
        """
        url = self.links['pullrequests']['href']

        data = pullrequest_data.generate_pullrequest_dictionary()

        response = self.connection.session.post(url, json=data)
        response.raise_for_status()

        pullrequest = Pullrequest(
            connection=self.connection,
            **response.json())

        return pullrequest

    def create_tag(self, tag_value: str, commit_hash: Union[str, "Commit"]) -> "Tag":
        url = self.links['tags']['href']

        data = {'name': tag_value}
        data = {
                'name': tag_value,
                'target': {'hash': commit_hash}
            }
        if isinstance(commit_hash, str):
            data['target'] = {'hash': commit_hash}
        elif isinstance(commit_hash, Commit):
            data['target'] = {'hash': commit_hash.hash}

        response = self.connection.session.post(url, json=data)
        response.raise_for_status()

        tag = Tag(
            connection=self.connection,
            **response.json())

        return tag


class PullrequestData():
    def __init__(self, title: str, source_branch: str, destination_branch: str, close_source_branch: bool = False):
        """Set data for creating a pullrequest in Bitbucket

        Args:
            title (str): The title of the pullrequest
            source_branch (str): The branch that has commits we want merged to the destination branch.
            destination_branch (str): The branch that has its history updated with commits.
            close_source_branch (bool): Pre-set the pullrequest to close the source branch if True.
                Leave the source branch open if False.
        """
        self.title = title
        self.source_branch = source_branch
        self.destination_branch = destination_branch
        self.close_source_branch = close_source_branch

    def generate_pullrequest_dictionary(self):
        data = {}
        if self.title:
            data['title'] = self.title
        else:
            data['title'] = self.source_branch

        data['source'] = {
            "branch": {
                "name": self.source_branch
            }
        }

        if self.destination_branch:
            data['destination'] = {
                "branch": {
                    "name": self.destination_branch
                }
            }

        if self.close_source_branch:
            data['close_source_branch'] = "true"

        return data


class PullrequestState(Enum):
    """
    Collection of options for requesting which pullrequests are retrieved
    from Bitbucket. Pullrequests that resulted in a merge, pullrequests that are
    superseded, pullrequests that are open or pullrequests that are declined.
    The left side of the statement is Bitbucket's name for a pullrequests's state.
    The right side of the statement is Branchmanagement's name for a pullrequest state.
    Example:
        import branchmanagement.bll.bitbucket
        branchmanagement.bll.bitbucket.method_call(
            branchmanagement.bll.bitbucket.PullrequestState('open'))
    """
    MERGED = 'merged'
    SUPERSEDED = 'superseded'
    OPEN = 'open'
    DECLINED = 'declined'


class PullrequestMergeStrategy(Enum):
    """
    Collection of options for requesting how source branch commits are added to the
    destination branch. Commits in a source branch can be added to a destination branch in
    different ways; merged, squashed or fast forwarded.
    The left side of the statement is Bitbucket's name for how commits are added to the destination.
    The right side of the statement is Branchmanagement's name for
        how commits are added to the destination.
    Example:
        import branchmanagement.bll.bitbucket
        branchmanagement.bll.bitbucket.method_call(
            branchmanagement.bll.bitbucket.PullrequestState('open'))
    """
    MERGE = 'merge_commit'
    SQUASH = 'squash'
    FAST_FORWARD = 'fast_forward'


class Tag(Base):
    """Helper class for Tags"""

    commits = commits_from_link

    @property
    def target_commit_object(self) -> Commit:
        """Commit object representing the tag

        Returns:
            Commit: object representing the tag
        """
        url = self.target['links']['self']['href']
        response = self.connection.session.get(url)

        commit = Commit(
            connection=self.connection,
            **response.json())

        return commit
