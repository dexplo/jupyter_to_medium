from io import BytesIO as StringIO
import matplotlib.pyplot as plt


def is_latex_cell(cell):

    # only look at markdown cells
    if cell["cell_type"] == "markdown":
        # get cell source
        s = cell["source"]
        if len(s) == 0:
            return False
        else:
            # cell sources are always strings
            # first let's try to convert to a list
            s_l = s.split("\n")
            if len(s_l) == 1:
                # then we only have a 1 liner
                if len(s) > 4 and s[:2] == "$$" and s[-2:] == "$$":
                    # then it's a latex block
                    return True
            else:
                # we have a multiline bit of source
                # check if top and bottom comments denote latex
                if len(s_l[0]) > 1 and s_l[0][:2] == "$$":
                    if len(s_l[-1]) > 1 and s_l[-1][-2:] == "$$":
                        return True
    # else we must just be a normal bit of source
    return False


def render_latex(formula, fontsize=10, dpi=200, format_="png"):
    """Renders LaTeX formula into image.
    """
    # set formatting
    mpl_context = {
        "text.usetex": False,
        "font.family": "serif",
        "mathtext.fontset": "dejavuserif",
        "font.serif": "Palatino",
        "font.weight": "light",
    }
    # use formatting and make text figure
    with plt.style.context(mpl_context):
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, u"${}$".format(formula), fontsize=fontsize)
    # create bytes buffer
    buffer_ = StringIO()
    # save fig to buffer and close it
    fig.savefig(
        buffer_,
        dpi=dpi,
        transparent=True,
        format=format_,
        bbox_inches="tight",
        pad_inches=0.0,
    )
    plt.close(fig)
    # return the bytes value of the fig - this is our photo'ed latex
    return buffer_.getvalue()


def format_single_line_latex(lt: str) -> str:

    # we want to do the following to a 1 liner
    # - remove '$$' from start and end
    lt = lt[2:][:-2]
    # - remove possible start/end whitespace
    if lt[0] == " ":
        lt = lt[1:]
    if lt[-1] == " ":
        lt = lt[:-1]
    # return it
    return lt


def replicate_alignment(lt: list) -> list:

    # new list with offset latex
    offset_lt = []
    found_first_equals = False
    offset = 0

    for line in lt:
        if "&=" in line:
            # check if this is the first
            if not found_first_equals:
                # then this is the first so find offset
                # factor of 1.5 if just because spaces tend to be
                # thinner than text
                offset = int(line.find("&=") * 1.35 // 1)
                found_first_equals = True
                # replace with normal equals
                offset_lt.append(line.replace("&=", "="))
            else:
                # we just need to replace
                replacement = r"\ " * offset + "="
                offset_lt.append(line.replace("&=", replacement))
        else:
            # just add it on
            offset_lt.append(line)
    return offset_lt


def format_multiline_latex(latex: list) -> str:

    # we have a multi-liner - we want to:
    # - remove the new lines, we will replace later
    lt = [x.replace("\n", "") for x in latex]
    # - remove latex new line \\ at end of lines
    lt = [x[:-2] if x[-2:] == r"\\" else x for x in lt]
    # - remove '$$' at top and bottom of list
    lt = [x for x in lt if x != "$$"]
    # - remove '$$' even if other latex on that line
    if "$$" in lt[0]:
        lt[0] = lt[0][2:]
    if "$$" in lt[-1]:
        lt[-1] = lt[-1][:-2]
    # - check if latex contains \begin and \end statements
    has_beg_end = ["\\begin" in x or "\\end" in x for x in lt]
    # - if so then we need to handle as mpl can't render
    if max(has_beg_end):
        # check if '{align}' is in the brackets
        has_align = ["align" in x for x in lt]
        # if aligns are present
        if max(has_align):
            # remove \begin{align } and \end{align}
            lt = [x for x in lt if x != "\\begin{align}"]
            lt = [x for x in lt if x != "\\end{align}"]
        else:
            # remove \begin{align } and \end{align}
            lt = [x for x in lt if "\\begin" in x]
            lt = [x for x in lt if "\\end" in x]

        # also flip '&=' to just '='
        # try and line up the alignment if there is some
        lt = replicate_alignment(lt)

    # finally format multi-line as single line
    l_out = []
    # need to add back '$' so mpl formats properly
    for c in lt:
        if lt.index(c) == 0:
            # if first line then don't add at start
            c = c + "$"
        elif lt.index(c) == (len(lt) - 1):
            # if last line then don't add at end
            c = "$" + c
        else:
            # if middles then add on both sides
            c = "$" + c + "$"
        l_out.append(c)
    # add back new line and return
    l_out = "\n".join(l_out)
    return l_out


def format_latex(latex: str) -> str:

    # seperate handling for one liners vs multi-liners
    latex = latex.split("\n")
    if len(latex) == 1:
        # then we have a 1 liner
        lt = format_single_line_latex(latex[0])
    else:
        # else multiline statement
        lt = format_multiline_latex(latex)
    return lt


def create_attachment_dict(cell, image):
    attach = {}
    image_name = cell["id"] + ".png"
    attach[image_name] = {"image/png": image}
    return attach
