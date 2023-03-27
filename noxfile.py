"""Script for nox sessions."""
import sys
from pathlib import Path
from textwrap import dedent

import nox

try:
    # uses poetry inside nox to ensure replicable
    # if not then only testing local installation of package
    # rather than testing by downloading the .whl and installing as per
    # pyproject.toml and then running tests
    # more info at official docs here:
    # https://github.com/cjolowicz/nox-poetry#why
    from nox_poetry import Session
    from nox_poetry import session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.
    Please install it using the following command:
    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None


# package name and to set which versions to run locally
# when run in github actions the following is passed
# --python=${{ matrix.python-version }}
# which dictates which version of python is run on each runner
package = "jupyter_to_medium"
python_versions = ["3.9", "3.8"]
nox.needs_version = ">= 2021.6.6"
# options for nox sessions
# again, github actions will pass one of these through the following lines
# env:
#      NOXSESSION: ${{ matrix.session }}
nox.options.sessions = ("tests",)


# runs test suite using pytest
# also returns coverage report
@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install("coverage[toml]", "pytest", "pygments")
    try:
        session.run(
            "coverage", "run", "--parallel", "-m", "pytest", *session.posargs
        )
    finally:
        # if being run by human and not CI process (GitHub Actions)
        if session.interactive:
            # then run the coverage (below) nox session
            session.notify("coverage", posargs=[])


# session to check coverage of tests
@session
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.install("coverage[toml]")

    # usually coverage tests run on different machines
    # when they run they dump coverage data into .coverage. path
    # this ensures that when run it combines all the files
    # see here:
    # https://coverage.readthedocs.io/en/stable/cmd.html#cmd-combine
    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)
