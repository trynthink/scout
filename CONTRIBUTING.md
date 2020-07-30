# Setup

For development, it is recommended to use:
- [pyenv](https://github.com/pyenv/pyenv#installation) for managing python versions
- [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv#installation) for managing packages and versions
- [pre-commit](https://pre-commit.com/#install) for managing code styling

1. Install `pyenv` and `pyenv-virtualenv` for your system
1. Install a python version through pyenv: `$ pyenv install 3.6.5`
1. Create a new `scout` specific environment: `$ pyenv virtualenv 3.6.5 scout`
1. Activate the environment in the root of the `path/to/scout`: `$ pyenv local scout`
1. Check it is set correctly: 
    ```
    user:scout user$ pyenv version
    scout (set by /Users/user/path/to//scout/.python-version)
    ```
1. Install dependencies: `$ pip install -r requirements.txt`
1. Activate pre-commit: `$ pre-commit install`
1. Check that pre-commit is installed: `$ pre-commit --version`
1. Check that tests are able to run: `$ py.test`
