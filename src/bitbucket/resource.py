"""Classes representing Bitbucket resources"""
import time
from enum import Enum
from types import SimpleNamespace
from typing import Union

import requests

from . import exceptions
from . import tool


class MixinBranchesFromLink(): # pylint: disable=too-few-public-methods
    """Mixin class used to add the ability to find multiple branches associated with the resource"""
    def branches(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving Branches from repository

        Returns:
            tool.Pages: Iterator that returns Branch objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['branches']['href'],
            resource=Branch,
            parameters=parameters)

        return pages


class MixinCommitsFromLink(): # pylint: disable=too-few-public-methods
    """Mixin class used to add querying for commits associated with object"""

    def commits(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving commits from the associated object

        Returns:
            tool.Pages: Iterator that returns commit objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['commits']['href'],
            parameters=parameters,
            resource=Commit)

        return pages


class MixinSourceFromLink(): # pylint: disable=too-few-public-methods
    """Mixin class used to add querying for source associated with object"""

    def source(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving source from the associated object

        Returns:
            tool.Pages: Iterator that returns commit_file objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['source']['href'],
            parameters=parameters,
            resource=CommitFile)

        return pages


class MixinStatusFromLink(): # pylint: disable=too-few-public-methods
    """Mixin class used to query commit statuses for a commit.
        Returns all statuses (e.g. build results) for a specific commit.
    """

    def statuses(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving commit statuses for a commit.

        Returns:
            tool.Pages: Iterator that returns build objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['statuses']['href'],
            parameters=parameters,
            resource=Build)

        return pages


class MixinPullrequestFromLink(): # pylint: disable=too-few-public-methods
    """Mixin to add the ability to query pullrequests associated with a resource"""
    def pullrequests(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving pullrequests from repository

        Returns:
            tool.Pages: Iterator that returns pullrequest objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['pullrequests']['href'],
            parameters=parameters,
            resource=Tag)

        return pages


class MixinTagsFromLink(): # pylint: disable=too-few-public-methods
    """Mixin to add querying tags associated with a resource"""
    def tags_from_link(self, parameters: dict=None) -> tool.Pages:
        """Method for retrieving tags from repository

        Returns:
            tool.Pages: Iterator that returns tag objects
        """
        pages = tool.Pages(
            connection=self.connection,
            url=self.links['tags']['href'],
            parameters=parameters,
            resource=Tag)

        return pages


class MixinDelete(): # pylint: disable=too-few-public-methods
    """Mixin class used to add delete functionality"""
    def delete(self) -> requests.models.Response:
        """Method for deleting the resource represented by this object.

        Returns:
            requests.models.Response: response returned by Bitbucket when
                delete is requested.
        """
        url = self.links['self']['href']
        response = self.connection.session.delete(url)
        response.raise_for_status()
        return response


class MixinDiffCommit(): # pylint: disable=too-few-public-methods
    """Mixin class used to add diff functionality"""
    def diff(self, commit_hash: Union[str, "Branch", "Commit", "Repository", None] = None) -> str:
        """Produces a raw git-style diff.

        If commit_hash is not included then the diff is produced against
            the first parent of the specified commit.
        If commit_hash is included then this produces a raw, git-style diff
            for a revspec of a commit, a branch's latest commit or a repository's latest commit.

        Args:
            commit_hash (Union[str, Branch, Commit, Repository, None): a commit hash as string,
                a Branch object's latest commit, a Commit object's hash or a Repositoryies last
                commit.

        Returns:
            str: the diff output returned by Bitbucket
        """
        source_hash = None
        if isinstance(self, Repository):
            commit = next(self.commits())
            source_hash = commit.hash
        elif isinstance(self, Branch):
            source_hash = self.target['hash']
        elif isinstance(self, Commit):
            source_hash = self.hash

        ### Handle different types of input
        destination_hash = None
        if isinstance(commit_hash, str):
            destination_hash = commit_hash
        if isinstance(commit_hash, Repository):
            commit = next(commit_hash.commits())
            destination_hash = commit.hash
        elif isinstance(commit_hash, Branch):
            destination_hash = commit_hash.target['hash']
        elif isinstance(commit_hash, Commit):
            destination_hash = commit_hash.hash

        spec = source_hash
        if destination_hash:
            spec = f"{source_hash}..{destination_hash}"

        url = '/'.join([
            self.connection.url_base,
            'diff',
            spec])

        response = self.connection.session.get(url)
        response.raise_for_status()

        return response.text

    def diffstat(
            self, commit_hash: Union[str, "Branch", "Commit", "Repository", None] = None) -> str:
        """Produces a record for every path modified, including
        information on the type of the change and the number of lines added and removed.

        If commit_hash is not included then the diff is produced
            against the first parent of the specified commit.
        If commit_hash is included then this produces a raw, git-style diff for a revspec of a
            commit, a branch's latest commit or a repository's latest commit.

        Args:
            commit_hash (Union[str, Branch, Commit, Repository, None): a commit hash as string,
                a Branch object's latest commit, a Commit object's hash or a Repositoryies last
                commit.

        Returns:
            str: the diff output returned by Bitbucket
        """
        source_hash = None
        if isinstance(self, Repository):
            commit = next(self.commits())
            source_hash = self.hash
        elif isinstance(self, Branch):
            source_hash = self.target['hash']
        elif isinstance(self, Commit):
            source_hash = self.hash

        ### Handle different types of input
        destination_hash = None
        if isinstance(commit_hash, str):
            destination_hash = commit_hash
        if isinstance(commit_hash, Repository):
            commit = next(commit_hash.commits())
            destination_hash = commit.hash
        elif isinstance(commit_hash, Branch):
            destination_hash = commit_hash.target['hash']
        elif isinstance(commit_hash, Commit):
            destination_hash = commit_hash.hash

        spec = source_hash
        if destination_hash:
            spec = f"{source_hash}..{destination_hash}"

        url = '/'.join([
            self.connection.url_base,
            'diffstat',
            spec])

        pages = tool.Pages(
            connection=self.connection,
            url=url,
            resource=Diffstat)

        return pages
        # response = self.connection.session.get(url)
        # response.raise_for_status()

        # return response


class Base(SimpleNamespace):
    """Base class for Bitbucket resources"""
    def __init__(self, connection: tool.Connection, **kwargs) -> None:
        super().__init__(**kwargs)

        self.connection = connection

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'

    def refresh(self):
        """Update a resource to capture changes that occurred after resource generation"""
        url = self.links['self']['href']

        response = self.connection.session.get(url)
        response.raise_for_status()

        self.__dict__.update(**response.json())


class Branch(MixinCommitsFromLink, MixinDelete, MixinDiffCommit, Base):
    """Helper class for Branches"""


class Build(Base):
    """Helper class for Builds.
        Object is returned from a commit's status link.
    """

    def commit_object(self, parameters: dict=None) -> "Commit":
        """Method for retrieving commit from the associated object

        Returns:
            commit: commit object associated with a build
        """
        response = self.connection.session.get(
            self.links['commit']['href'],
            params=parameters)

        response.raise_for_status()

        commit = Commit(
            connection=self.connection,
            **response.json())

        return commit


class Commit(MixinDiffCommit, MixinStatusFromLink, Base):
    """Class representing a commit in Bitbucket"""

    def __repr__(self):
        return f'{self.__class__.__name__}(hash={self.hash})'


class Diffstat(Base):
    """Helper class for diffstat"""

    def __repr__(self):
        return f"{self.__class__.__name__} {self.old['path']}:{self.new['path']}"


class CommitFile(Base):
    """Helper class for commit_file"""

    def __repr__(self):
        return f'{self.__class__.__name__} {self.path}'

    def commit_object(self) -> Commit:
        """Commit object representing the merging of two histories done
        through a pullrequest.

        Returns:
            Commit: object representing the merging of two histories
        """
        url = self.commit['links']['self']['href']
        response = self.connection.session.get(url)

        commit = Commit(
            connection=self.connection,
            **response.json())

        return commit


class Pipeline(Base):
    """Helper class for Pipelines"""

    def __repr__(self):
        representation = (
            f"<{self.__class__.__name__} {self.repository['name']}"
            f"{self.build_number} {self.target['ref_name']}>")
        return representation


class Pullrequest(MixinCommitsFromLink, Base):
    """Helper class for Pullrequests"""

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'

    def merge(
            self, merge_strategy: "PullrequestMergeStrategy",
            message: str) -> Union["Pullrequest", "PullrequestWaiter"]:
        """Merge an open pullrequest

        Returns:
            Union["Pullrequest", "PullrequestWaiter"]: Either a pullrequest waiter if the merge
                is occurring asynchronously on Bitbucket's side or a closed pullrequest.
        """
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
    """Class instantiated when a pullrequest is merged asynchronously"""
    def __init__(self, connection: tool.Connection, location: str):
        self.connection = connection
        self.location = location

    def ready(self):
        """Determine if a pullrequest's merge request has completed"""
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
        """Get the status of a pullrequest"""
        poll_merge = self.connection.session.get(
            self.location)

        return poll_merge

    def wait(self, delay: int = 5, max_attempts: int = 40):
        """Wait for a asynchronous pullrequest to complete

        Args:
            delay (int, optional): How long to wait between polling. Defaults to 5.
            max_attempts (int, optional): How many poll attempts to make. Defaults to 40.
        """
        for attempt in range(0, max_attempts): #pylint: disable=unused-variable
            time.sleep(delay)

            poll_merge = self.connection.session.get(self.location)

            if poll_merge.json().get('task_status') == 'PENDING':
                continue

            if poll_merge.status_code == 400:
                break

            if poll_merge.json().get('task_status') == 'SUCCESS':
                break


class Repository(
        MixinBranchesFromLink, MixinCommitsFromLink, MixinDiffCommit,
        MixinPullrequestFromLink, MixinSourceFromLink, MixinTagsFromLink, Base):
    """Helper class for Repositories"""

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

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise exceptions.ObjectDoesNotExist(*error.args, **error.__dict__) from error

        pullrequest = Pullrequest(
            connection=self.connection,
            **response.json())

        return pullrequest

    def branch(self, branch_name) -> Branch:
        """Method for retrieving a single branch object

        Args:
            branch_name (str): The name of the branch

        Returns:
            Branch: a single branch object matching the parameter
                branch_name found within the repository.
        """
        url = '/'.join([
            self.links['branches']['href'],
            branch_name])

        response = self.connection.session.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise exceptions.ObjectDoesNotExist(*error.args, **error.__dict__) from error

        branch = Branch(
            connection=self.connection,
            **response.json())

        return branch

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

    def create_tag(self, tag_name: str, commit_hash: Union[str, "Commit"]) -> "Tag":
        """Method for creating a tag in a Bitbucket repository

        Raises:
            exceptions.ObjectExists: exception thrown when the tag already exists.

        Returns:
            Tag: object representing a Tag in Bitbucket
        """
        url = self.links['tags']['href']

        data = {'name': tag_name}

        if isinstance(commit_hash, str):
            data['target'] = {'hash': commit_hash}
        elif isinstance(commit_hash, Commit):
            data['target'] = {'hash': commit_hash.hash}

        response = self.connection.session.post(url, json=data)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            if 'application/json' in response.headers['Content-Type']:
                if 'already exists' in response.json().get('error', {}).get('message'): # pylint: disable=no-else-raise
                    raise exceptions.ObjectExists(*error.args, **error.__dict__) from error
                else:
                    raise
            else:
                raise

        tag = Tag(
            connection=self.connection,
            **response.json())

        return tag

    def create_branch(self, branch_name: str, commit_hash: Union[str, "Commit"]) -> Branch:
        """Method for creating a git branch in the associated repository

        Args:
            branch_name (str): The name of the branch
            commit_hash (str, optional): short or long commit hash. Defaults to "default".

        Returns:
            Branch: branch object representing a newly created git branch in the repository.
        """
        url = self.links['branches']['href']

        data = {'name': branch_name}

        if isinstance(commit_hash, str):
            data['target'] = {'hash': commit_hash}
        elif isinstance(commit_hash, Commit):
            data['target'] = {'hash': commit_hash.hash}

        response = self.connection.session.post(url, json=data)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            if 'application/json' in response.headers['Content-Type']:
                if 'already exists' in response.json().get('error', {}).get('message'): # pylint: disable=no-else-raise
                    raise exceptions.ObjectExists(*error.args, **error.__dict__) from error
                else:
                    raise
            else:
                raise

        branch = Branch(
            connection=self.connection,
            **response.json())

        return branch

    def tag(self, tag_name: str) -> "Tag":
        """Method for retrieving a single tag object

        Args:
            tag_name (str): The name of the tag

        Returns:
            Tag: a single branch object matching the parameter
                tag_name found within the repository.
        """
        url = '/'.join([
            self.links['tags']['href'],
            tag_name])

        response = self.connection.session.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise exceptions.ObjectDoesNotExist(*error.args, **error.__dict__) from error

        tag = Tag(
            connection=self.connection,
            **response.json())

        return tag


class PullrequestData(): # pylint: disable=too-few-public-methods
    """Class used to represent and generate the data required to make a pullrequest"""
    def __init__(
            self, title: str, source_branch: str,
            destination_branch: str, close_source_branch: bool = False):
        """Set data for creating a pullrequest in Bitbucket

        Args:
            title (str): The title of the pullrequest
            source_branch (str): The branch that has commits
                we want merged to the destination branch.
            destination_branch (str): The branch that has its history updated with commits.
            close_source_branch (bool): Pre-set the pullrequest to close the source branch if True.
                Leave the source branch open if False.
        """
        self.title = title
        self.source_branch = source_branch
        self.destination_branch = destination_branch
        self.close_source_branch = close_source_branch

    def generate_pullrequest_dictionary(self) -> dict:
        """Create the dictionary of data required to make a pullrequest

        Returns:
            dict: dictionary of data to make a pullrequest
        """
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
    """Collection of options for requesting how source branch commits are added to the
    destination branch.

    Commits in a source branch can be added to a destination branch in
    different ways; merged, squashed or fast forwarded.
    The left side of the statement is Bitbucketpy's name
        for how commits are added to the destination.
    The right side of the statement is Bitbucket's name
        for how commits are added to the destination.

    Example:
        import bitbucket
        repository = bitbucket.get_repository('repository nane')
        pullrequest = repository.pullrequest(1)
        pullrequest.merge(bitbucket.resource.PullrequestMergeStrategy.FAST_FORWARD, 'test merge')
    """
    MERGE = 'merge_commit'
    SQUASH = 'squash'
    FAST_FORWARD = 'fast_forward'


class Tag(MixinCommitsFromLink, MixinDelete, Base):
    """Helper class for Tags"""

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
