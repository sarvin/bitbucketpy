# bitbucketpy
WIP Python package for interacting with Bitbucket Cloud's API.

## Usage
You'll need three items:

* EMAIL: The email address used to interact with Bitbucket.
* PASSWORD: An API key used to authenticate with Bitbucket.
* API_ENDPOINT: ex https://api.bitbucket.org/2.0

### Interact with the [repository API](https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Bworkspace%7D/%7Brepo_slug%7D#get)
```python
import bitbucket
api = bitbucket.API(WORKSPACE, EMAIL, PASSWORD)
repository = api.get_repository(REPOSITORY_NAME)
```

#### Get branches in repository
```python
branches = repository.branches()
for branch in branches:
    print(branch.name)
```

#### The latest commit on a branch
```python
commit = next(branch.commits)
```

#### Find commits ahead of master
```python
feature_branch = repository.branch('feature_branch_name')

commits = [
    commit
    for commit in feature_branch.commits({'exclude': 'master', 'pagelen': 100})
]

print(f"feature_branch_name is {len(commits)} commits ahead of master")
```

#### Find a tag in the repository
```python
tag = repository.tag('1.0.0')
```

#### Find pipelines for a branch

```python
pipelines = list(api.get_pipelines(
    'REPO_SLUG',
    {
        'target.branch':'BRANCH_NAME',
        'sort': '-created_on',
        'pagelen':20}))
```
