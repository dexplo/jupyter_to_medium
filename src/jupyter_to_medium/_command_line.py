import argparse
import sys


class CustomFormatter(argparse.RawTextHelpFormatter):
    pass


HELP = """\n\n
          ========================================================

                              jupyter_to_medium

          ========================================================

Publish Jupyter Notebooks as Medium Blog posts.

Request an integration token from Medium first!
===============================================

https://github.com/Medium/medium-api-docs

Required Positional Arguments
=============================

filename
    The filename of the notebook you wish to publish to Medium

Optional Keyword Arguments
==========================

--integration-token
    When `None`, the integration token must be stored in a file
    located in the users home directory at
    '.jupyter_to_medium/integration_token'. You'll need to create
    this directory and file first and paste your token there.

    Otherwise, pass the integration token directly as a string.

    Learn how to get an integration token from Medium.
    https://github.com/Medium/medium-api-docs
    (default: None)

--pub-name
    Name of Medium publication. Not necessary if publishing as a user.
    (default: None)

--title
    This title is used for SEO and when rendering the post as a listing,
    but will not appear in the actual post. Use the first cell of the
    notebook with an H1 markdown header for the title.
    i.e. # My Actual Blog Post Title

    Leave as `None` to use the filename as this title
    (default: None)

--tags
    String of tags to help classify your post. Place each tag in one
    string separated by a comma. Only the first five will be used.
    i.e. "python, jupyter, data science, machine learning"
    Tags longer than 25 characters will be ignored.
    (default: None)

--publish-status
    The status of the post. Valid values are 'public', 'draft', or 'unlisted'.
    Only draft will be allowed for now. Finalize publication on Medium.
    (default: 'draft')

--notify-followers
    Whether to notify followers that the user has published.
    True or False (default: False)

--license
    The license of the post. Valid values are 'all-rights-reserved',
    'cc-40-by', 'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd',
    'cc-40-by-nc-sa', 'cc-40-zero', 'public-domain'.
    (default: all-rights-reserved)

--canonical-url
    A URL of the original home of this content, if it was originally
    published elsewhere. i.e. https://dunderdata.com/blog/bar_chart_race
    It must begin with 'http' (default: None)

--chrome-path
    Path to your machine's chrome executable. By default, it is
    automatically found. Use this when chrome is not automatically found.
    (default: None)

--save-markdown
    Whether or not to save the markdown and corresponding image files. They
    will be placed in the same folder containing the notebook. The images will
    be in a folder with _files appended to it. True or False (default: False)

--table-conversion
    Medium does not render tables correctly such as pandas DataFrame.
    As a workaround, images of the tables will be produced in their place.
    When 'chrome', a screenshot using the Chrome web browser will be used.
    When 'matplotlib', the matplotlib table function will be used to
    produce the table.
    Valid values are 'chrome' or 'matplotlib' (default: 'chrome')

--gistify
    Medium has poor formatting for embedded code. To prevent chunks of code
    showing unformatted in an article, this option will automatically create
    gists for you and embed them in your article. This requires you to first
    generate a Personal Access Token (PAT) on github that is then used,
    similar to the Medium Integration Token, to create the gists.

--gist-threshold
    If chosen to use gists for code blocks, this sets the length in lines of
    code for which to make code blocks into gists. This is to prevent gists of
    only several lines unless desired.
    
--public-gists
    Whether to create the gists as public (can be found by search engines)
    or private (only accessible through link).

Examples
========

jupyter_to_medium my_notebook.ipynb --tags="python, networking, asyncio"

Created by Ted Petrou (https://www.dunderdata.com)

"""

parser = argparse.ArgumentParser(formatter_class=CustomFormatter, add_help=False, usage=argparse.SUPPRESS)
parser.add_argument("filename", default=False)
parser.add_argument("-h", "--help", action="store_true", dest="help")
parser.add_argument("--integration-token", type=str)
parser.add_argument("--pub-name", type=str)
parser.add_argument("--title", type=str)
parser.add_argument("--tags", type=str)
parser.add_argument("--publish-status", type=str, choices=["draft"], default="draft")
parser.add_argument("--notify-followers", type=bool, default=False)
parser.add_argument(
    "--license",
    type=str,
    choices=[
        "all-rights-reserved",
        "cc-40-by",
        "cc-40-by-sa",
        "cc-40-by-nd",
        "cc-40-by-nc",
        "cc-40-by-nc-nd",
        "cc-40-by-nc-sa",
        "cc-40-zero",
        "public-domain",
    ],
    default="all-rights-reserved",
)
parser.add_argument("--canonical-url", type=str)
parser.add_argument("--chrome-path", type=str)
parser.add_argument("--save-markdown", type=bool, default=False)
parser.add_argument(
    "--table-conversion",
    type=str,
    choices=["chrome", "matplotlib"],
    default="chrome",
)
parser.add_argument("--gistify", type=bool, default=False)
parser.add_argument("--gist-threshold", type=int, default=5)
parser.add_argument("--public-gists", type=bool, default=False)


def main():
    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        print(HELP)
    else:
        args = vars(parser.parse_args())
        if args["tags"]:
            args["tags"] = [tag.strip() for tag in args["tags"].split(",")[:5]]
        del args["help"]
        from ._publish_to_medium import publish

        publish(**args)
