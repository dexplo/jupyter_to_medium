import json
from pathlib import Path

import requests

# define github api up top
GITHUB_API = "https://api.github.com"


def write_file(file_name, new_content):
    f = open(file_name, "w")
    f.write(new_content)
    f.close()


def get_github_api_token(tok):
    """
    Fetch github personal access token (PAT) for gist api request using POST
    Parameters
    ----------
    tok : str
        PAT if passed as string, else None and will be fetched
    """
    if not tok:
        tok_path = Path.home() / ".jupyter_to_medium" / "github_token"
        tok = open(tok_path).read().splitlines()[0]
    return tok


def get_formatted_gist_code(response, output_type):
    """
    Parse gist api response and return desired output
    For medium, this is an http url for embedded the gist
    Parameters
    ----------
    response : json
        gist api response from the POST request to create gist
    output_type: str
        desired publication name
    """
    if output_type == "hugo":
        owner = response["owner"]["login"]
        gist_id = response["id"]
        short_code = "{{< gist " + owner + " " + gist_id + " >}}"
        return short_code
    else:
        return response["html_url"]


def create_gists(gists, description, output_type="medium", github_token=None, public=True):
    """
    Takes code strings, creates a single gist with multiple files,
    returns url for publication embedding
    Can see git ref here:
    https://docs.github.com/en/rest/reference/gists#create-a-gist
    Parameters
    ----------
    gists: list
        a list of tuples: (gist file name, content)
    description: str
        gist description - by default the space-stripped notebook title
        e.g. 'My New Article' --> MyNewArticle
    output_type: str
        desired publication name
    github_token: str
        can pass github personal access token
        else defaults to ~/.jupyter_to_medium/github_token
    public: bool
        whether to create the gist as public (True) or secret (False)
        Note: secret gists can be accessed by knowing their exact url.
        From github docs:
        " Public gists show up in Discover, where people can browse new gists as
          they're created. They're also searchable, so you can use them if you'd
          like other people to find and see your work. Secret gists don't show up
          in Discover and are not searchable. Secret gists aren't private."
    """
    GITHUB_API = "https://api.github.com"
    try:
        api_token = get_github_api_token(github_token)
    except Exception:
        raise ValueError(
            "Problem fetching Github Token \n \
                Ensure it is located in ~/.jupyter_to_medium/github_token"
        )

    # form a request URL
    url = GITHUB_API + "/gists"
    # headers, parameters, payload
    headers = {"Authorization": f"token {api_token}"}
    params = {"scope": "gist"}
    files = {fn: {"content": content} for fn, content in gists}
    payload = {
        "description": description,
        "public": public,
        "files": files,
    }
    # make a request
    res = requests.post(url, headers=headers, params=params, data=json.dumps(payload))
    # if 201 response, then proceed, else fail with error
    try:
        # success with gist creation
        j = json.loads(res.text)
        output = get_formatted_gist_code(j, output_type)
    except Exception:
        raise ValueError(f"Problem with gistify-ing:\n {res.text}")

    return output


def gist_namer(art_title, num):
    """
    Create formatted gist name to help with grouping gists
    Parameters
    ----------
    art_title : str
        defaults to the notebook name
    num: int
        gist count for this article e.g. first gist of article is 0
    """
    # lower case and snake_case the whole thing
    title = art_title.lower().replace(" ", "_")
    title += str(num)
    return title


def gistPostprocessor(
    markdown_list,
    art_title,
    lang_ext=".py",
    output_type="medium",
    gist_threshold=5,
    public=True,
):
    """
    Iterate over listify'ed markdown, identify code, insert gist http instead
    Overall to remove unlinted codeblocks from .md for medium publication
    To be called after converting an .ipynb to .md format
    Parameters
    ----------
    markdown_list : list
        list of strings created by \n splitting a standard .md document
    art_title: str
        title of the article - used to describe gists
    output_type: str
        desired publication name e.g. 'medium'
    gist_threshold: int
        only gistify code snippets with a line length greater than this
    """

    new_md_str = ""
    code_block_started = False
    code_block = []
    # We will collect all parts in this list, before saving them to the same gist:
    gists = []
    PLACEHOLDER = "@PLACEHOLDER_FOR_GIST_URL4321@"

    for line in markdown_list:
        if line.startswith("```") and not code_block_started:
            # we must have the start of a new code block
            code_block_started = True
        elif line.startswith("```") and code_block_started:
            # we must have the end of a code block
            # check if code block is greater than threshold
            lcb = len(code_block)
            # convert code block list to string
            code_block = "".join(code_block)

            # Skip empty cells:
            if code_block.replace("\n", "") != "":
                if lcb > gist_threshold:

                    # The filename within the gist:
                    fn = "part_%02i%s" % (len(gists) + 1, lang_ext)

                    gists.append((fn, code_block))

                    # We don't know the gist url yet, as it is not created. So we only use a
                    # placeholder, which we will later replace:
                    new_md_str += f"\n{PLACEHOLDER}?file={fn}\n "

                else:
                    # let's keep it as it is, we need to add back the ```
                    new_md_str += "```\n" + code_block + "```\n"
            # reset our looping vars
            code_block = []
            code_block_started = False
        elif code_block_started:
            # add code to the code_block until we hit the end of the block
            # increment block length
            code_block.append(line)
        else:
            # non-code markdown so just add it
            new_md_str += line

    # time to gistify the code we have
    url = create_gists(gists, art_title, output_type=output_type, public=public)
    new_md_str = new_md_str.replace(PLACEHOLDER, url)
    # return our new markdown and the url
    return new_md_str, url
