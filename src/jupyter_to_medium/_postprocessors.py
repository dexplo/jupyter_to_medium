import json
from pathlib import Path
import requests
import uuid


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
        id = response["id"]
        short_code = "{{< gist " + owner + " " + id + " >}}"
        return short_code
    else:
        return response["html_url"]


def create_gist(
    title, description, content, output_type="medium", github_token=None, public=True,
):
    """
    Takes code string, creates gist, returns url for publication embedding
    Can see git ref here:
    https://docs.github.com/en/rest/reference/gists#create-a-gist
    Parameters
    ----------
    title : str
        gist title - by default a random uuid with notebook lang ext (e.g. .py)
        added so gist has desired linting
    description: str
        gist description - by default the space-stripped notebook title with _n
        e.g. 'My New Article' --> MyNewArticle_0 for first gist in notebook
    content: str
        str code block to be made into gist from markdown
    output_type: str
        desired publication name
    github_token: str
        can pass github personal access token
        else defaults to ~/.jupyter_to_medium/github_token
    """
    GITHUB_API = "https://api.github.com"
    try:
        API_TOKEN = get_github_api_token(github_token)
    except Exception:
        raise ValueError(
            "Problem fetching Github Token \n \
                Ensure it is located in ~/.jupyter_to_medium/github_token"
        )

    # form a request URL
    url = GITHUB_API + "/gists"
    # headers, parameters, payload
    headers = {"Authorization": "token %s" % API_TOKEN}
    params = {"scope": "gist"}
    payload = {
        "description": description,
        "public": public,
        "files": {title: {"content": content}},
    }
    # make a request
    res = requests.post(
        url, headers=headers, params=params, data=json.dumps(payload)
    )
    # if 201 response, then proceed, else fail with error
    try:
        # success with gist creation
        j = json.loads(res.text)
        output = get_formatted_gist_code(j, output_type)
    except Exception:
        raise ValueError("Problem with gistify-ing:\n" + res.text)

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

    gist_dict = {}
    new_md_str = ""
    code_block_started = False
    code_block = []
    gist_count = 0
    code_block_length = 0

    for line in markdown_list:
        if line.startswith("```") and not code_block_started:
            # we must have the start of a new code block
            code_block_started = True
        elif line.startswith("```") and code_block_started:
            # we must have the end of a code block
            # check if code block is greater than threshold
            if len(code_block) > gist_threshold:
                # convert code block list to string
                code_block = "".join(code_block)
                # let's replace it with a gist
                # time to gistify the code we have
                gist_name = gist_namer(art_title, gist_count)
                short_code = create_gist(
                    str(uuid.uuid4()) + lang_ext,
                    gist_name,
                    code_block,
                    output_type,
                    public=public
                )
                # now add to our new md string
                new_md_str += "\n" + short_code + "\n"
                # update gist_dict
                gist_dict[short_code] = code_block
                # update gist count
                gist_count += 1
            else:
                # let's keep it as it is, we need to add back the ```
                code_block = "".join(code_block)
                new_md_str += "```\n" + code_block + "```\n"
            # reset our looping vars
            code_block_length = 0
            code_block = []
            code_block_started = False
        elif code_block_started:
            # add code to the code_block until we hit the end of the block
            # increment block length
            code_block.append(line)
            code_block_length += 1
        else:
            # non-code markdown so just add it
            new_md_str += line

    # return our new markdown and the gist_dict
    return new_md_str, gist_dict
