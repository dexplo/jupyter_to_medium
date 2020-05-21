import argparse
import textwrap
import sys

class CustomFormatter(argparse.RawTextHelpFormatter):
    pass

HELP = '''\n\n
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

--integration-token : str, default None
    When `None`, the integration token must be stored in a file
    located in the users home directory at 
    '.jupyter_to_medium/integration_token'. You'll need to create 
    this directory and file first and paste your token there.

    Otherwise, pass the integration token directly as a string.

    Learn how to get an integration token from Medium.
    https://github.com/Medium/medium-api-docs
    
--pub-name : str, default `None`
    Name of Medium publication. Not necessary if publishing as a user.
    
--title : str, default `None`
    Title of the Medium post. Leave as `None` to use the name 
    of the notebook as the title.

--tags : list of strings, default `None`
    List of tags to classify the post. Only the first five will be used. 
    Tags longer than 25 characters will be ignored.

--publish-status : str, default 'draft'
    The status of the post. Valid values are 'public', 'draft', or 'unlisted'.

--notify-followers : bool, default False
    Whether to notify followers that the user has published.

--license : str, default 'all-rights-reserved'
    The license of the post. Valid values are 'all-rights-reserved', 'cc-40-by', 
    'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 
    'cc-40-zero', 'public-domain'. The default is 'all-rights-reserved'.

--canonical-url : str, default `None`
    A URL of the original home of this content, if it was originally 
    published elsewhere.

--chrome-path : str, default `None`
    Path to your machine's chrome executable. By default, it is 
    automatically found. Use this when chrome is not automatically found.

--download-markdown
    Whether or not to download the markdown and corresponding image files. They 
    will be placed in the same folder containing the notebook. The images will be
    in a folder with _files appended to it.


Examples
========

jupyter_to_medium my_notebook.ipynb

Created by Ted Petrou (https://www.dunderdata.com)

'''

parser = argparse.ArgumentParser(formatter_class=CustomFormatter, add_help=False, usage=argparse.SUPPRESS)
parser.add_argument('filename', default=False)
parser.add_argument('-h', '--help', action='store_true', dest='help')
parser.add_argument('--integration-token', type=str)
parser.add_argument('--pub-name', type=str)
parser.add_argument('--title', type=str)
parser.add_argument('--tags', type=list)
parser.add_argument('--publish_status', type=str, choices=['draft', 'public', 'unlisted'], default='draft')
parser.add_argument('--notify-followers', type=bool, default=False)
parser.add_argument('--license', type=str, choices=['all-rights-reserved', 'cc-40-by', 
    'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 
    'cc-40-zero', 'public-domain'], default='all-rights-reserved')
parser.add_argument('--canonical-url', type=str)
parser.add_argument('--chrome-path', type=str)
parser.add_argument('--download-markdown', type=bool, default=False)

def main():
    if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
        print(HELP)
    else:
        args = vars(parser.parse_args())
        del args['help']
        from ._publish_to_medium import publish
        convert(**args)
