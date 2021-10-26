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

### Find a tag in the repository
```python
tag = repository.tag('1.0.0')
```
