import base64
from pathlib import Path
import re

import mistune
from nbconvert.preprocessors import Preprocessor
import requests

from ._latex import create_attachment_dict
from ._latex import is_latex_cell
from ._latex import render_latex
from ._latex import format_latex


def get_image_files(md_source, only_http=False):
    """
    Return all image files from a markdown cell

    Parameters
    ----------
    md_source : str
        Markdown text from cell['source']
    """
    pat_inline = r"\!\[.*?\]\((.*?\.(?:gif|png|jpg|jpeg|tiff|svg))"
    pat_ref = r"\[.*?\]:\s*(.*?\.(?:gif|png|jpg|jpeg|tiff|svg))"
    inline_files = re.findall(pat_inline, md_source)
    ref_files = re.findall(pat_ref, md_source)
    possible_image_files = inline_files + ref_files
    image_files = []
    for file in possible_image_files:
        p = file.strip()
        is_http = p.startswith("http://") or p.startswith("https://")
        is_attachment = p.startswith("attachment")
        if p not in image_files:
            if is_http:
                if only_http:
                    image_files.append(p)
            elif not (is_attachment or only_http):
                image_files.append(p)
    return image_files


def replace_md_tables(image_data_dict, md_source, converter, cell_index):
    i = 0
    table = re.compile(r"^ *\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n*", re.M)
    nptable = re.compile(r"^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n*", re.M)

    def md_table_to_image(match):
        nonlocal i
        md = match.group()
        html = mistune.markdown(md, escape=False)
        html = "<div>" + html + "</div>"
        image_data = base64.b64decode(converter(html))
        new_image_name = f"markdown_{cell_index}_table_{i}.png"
        image_data_dict[new_image_name] = image_data
        i += 1
        return f"![]({new_image_name})\n"

    md_source = nptable.sub(md_table_to_image, md_source)
    md_source = table.sub(md_table_to_image, md_source)
    return md_source


def get_image_tags(md_source, only_http=False):
    pat_img_tag = r"""(<img.*?[sS][rR][Cc]\s*=\s*['"](.*?)['"].*?/>)"""
    img_tag_files = re.findall(pat_img_tag, md_source)

    kept_files = []
    for entire_tag, src in img_tag_files:
        is_http = src.startswith("http://") or src.startswith("https://")
        if is_http:
            if only_http:
                kept_files.append((entire_tag, src))
        elif not only_http:
            kept_files.append((entire_tag, src))

    return kept_files


class LatexPreprocessor(Preprocessor):
    def preprocess_cell(self, cell, resources, cell_index):
        # check if this is a latex cell
        if is_latex_cell(cell):
            # then we need to convet
            latex = cell["source"]
            # create it and render it
            latex_fmt = format_latex(latex)
            latex_rendered = render_latex(latex_fmt)
            # now we need to create a temp file to store it it
            # create encoded str as will decode when processing attachments
            img_str = base64.b64encode(latex_rendered)
            # create data for the attachment dict
            attach_dict = create_attachment_dict(cell, img_str)
            cell["attachments"] = attach_dict
            cid = cell["id"]
            cell["source"] = f"![{cid}.png](attachment:{cid}.png)"

        return cell, resources


class MarkdownPreprocessor(Preprocessor):
    # this function overrides the default function for Preprocessor
    def preprocess_cell(self, cell, resources, cell_index):
        # get the notebook path set by get_resources already
        nb_home = Path(resources["metadata"]["path"])
        # get image_data_dict - this starts as blank then gets populated
        # as we go through the cells and find cells which we think contain
        # images, tables that *should* be images etc
        image_data_dict = resources["image_data_dict"]
        if cell["cell_type"] == "markdown":
            # find all images in this cell using regex
            all_image_files = get_image_files(cell["source"])

            # for each image file path identified
            for i, image_file in enumerate(all_image_files):
                ext = Path(image_file).suffix
                # correct ext to jpeg if required
                if ext.startswith(".jpg"):
                    ext = ".jpeg"
                # new name for the image in the markdown
                new_image_name = f"markdown_{cell_index}_normal_image_{i}{ext}"

                # if embedded from web link then use requests to grab data
                # only grab from secure urls
                if "https://" in image_file:
                    response = requests.get(image_file, timeout=60)
                    if response.status_code == 200:
                        image_data = response.content
                    else:
                        # unsuccessful request
                        print(f"Unsuccessful request for image: {image_file}")
                else:
                    # read the image data in from the file path
                    image_data = open(nb_home / image_file, "rb").read()
                # replace the image name in the markdown with the new name
                cell["source"] = cell["source"].replace(image_file, new_image_name)
                # add this image to the dict
                image_data_dict[new_image_name] = image_data

            # find HTML <img> tags
            # do the same as the above but for images embedded in html tags
            all_image_tag_files = get_image_tags(cell["source"])
            for i, (entire_tag, src) in enumerate(all_image_tag_files):
                ext = Path(src).suffix
                if ext.startswith(".jpg"):
                    ext = ".jpeg"
                new_image_name = f"markdown_{cell_index}_local_image_tag_{i}{ext}"
                image_data = open(nb_home / src, "rb").read()
                image_data_dict[new_image_name] = image_data
                cell["source"] = cell["source"].replace(entire_tag, f"![]({new_image_name})")

            # find images attached to markdown through dragging and dropping
            # this is because those images will have 'attachements' key
            # in the dict for their cell
            attachments = cell.get("attachments", {})
            for i, (image_name, data) in enumerate(attachments.items()):
                # I think there is only one image per attachment
                # Though there can be multiple attachments per cell
                # So, this should only loop once
                for j, (mime_type, base64_data) in enumerate(data.items()):
                    ext = mime_type.split("/")[-1]
                    if ext == "jpg":
                        ext = "jpeg"
                    new_image_name = f"markdown_{cell_index}_attachment_{i}_{j}.{ext}"
                    # decode the image data and add to overall image dict
                    image_data = base64.b64decode(base64_data)
                    image_data_dict[new_image_name] = image_data
                    cell["source"] = cell["source"].replace(f"attachment:{image_name}", new_image_name)

            # find markdown tables
            cell["source"] = replace_md_tables(
                image_data_dict,
                cell["source"],
                resources["converter"],
                cell_index,
            )

        return cell, resources


# converts DataFrames to images when not executing notebook first
# also converts gifs to png for outputs since jinja template is missing this
# could write a custom template to handle this
class NoExecuteDataFramePreprocessor(Preprocessor):
    def preprocess_cell(self, cell, resources, index):
        converter = resources["converter"]
        if cell["cell_type"] == "code":
            outputs = cell.get("outputs", [])
            for output in outputs:
                if "data" in output:
                    has_image_mimetype = False
                    for key, value in output["data"].items():
                        if key.startswith("image"):
                            has_image_mimetype = True
                            if key == "image/gif":
                                # gifs not in jinja template
                                key = "image/png"
                            output["data"] = {key: value}
                            break

                    if not has_image_mimetype and "text/html" in output["data"]:
                        html = output["data"]["text/html"]
                        if "</table>" in html and "</style>" in html:
                            output["data"] = {"image/png": converter(html)}
                        elif html.startswith("<img src"):
                            # TODO: Necessary when images
                            # from IPython.display module used
                            pass
        return cell, resources
