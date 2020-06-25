import io
import base64
import textwrap

import pandas as pd
import matplotlib.pyplot as plt


def html_to_df(html):
    append = False

    try:
        df_new = pd.read_html(html, index_col=0)[0]
        append = True
    except:
        df_new = pd.read_html(html)[0]
        
    if isinstance(df_new.columns, pd.MultiIndex):
        bottom_level = df_new.columns.get_level_values(-1).tolist()

        # assume that once Unnamed starts end of index
        idx_names = []
        for val in bottom_level:
            if val.startswith('Unnamed:'):
                break
            idx_names.append(val)
            
        n = len(df_new.columns.levels)
        m = len(idx_names)
        col_values = []
        for i in range(n - 1):
            col_values.append(df_new.columns.get_level_values(i).tolist()[m:])
            
        if len(col_values) == 1:
            columns = col_values[0]
        else:
            columns = pd.MultiIndex.from_tuples([col for col in zip(*col_values)])

        df_new.columns = idx_names + list(range(len(columns)))
        df_new = df_new.set_index(idx_names, append=append)
        df_new.columns = columns
    return df_new

def get_col_widths(df):
    col_len = []
    total = 0
    for col in df.columns:
        vals = df[col].astype(str)
        max_len = max(7, len(str(col)))
        for val in vals:
            cur_len = len(val)
            if cur_len > max_len:
                max_len = cur_len
        col_len.append(max_len)
        total += max_len

    col_len = [c / total for c in col_len]
    return col_len


def handle_decimal(x, wrap=False, width=12):
    if wrap:
        try:
            return textwrap.fill(x, width, break_long_words=False)
        except:
            return textwrap.fill(str(x), width, break_long_words=False)
    else:
        vals = str(x).split('.')
        if len(vals) == 1:
            return vals[0]
        else:
            vals[1] = vals[1][:5]
            return '.'.join(vals)


def get_values(df, wrap_width):
    for col in df.columns.tolist():
        wrap = df[col].dtype.kind not in ('i', 'f')
        df[col] = df[col].apply(handle_decimal, wrap=wrap, width=wrap_width)
    return df.values.tolist()


def crop_image(buffer):
    from PIL import Image, ImageChops
    img = Image.open(buffer)

    img_gray = img.convert('L')
    bg = Image.new('L', img.size, 255)
    diff = ImageChops.difference(img_gray, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()

    x0, y0, x1, y1 = bbox
    x0 = min(x0, int(img.size[0] * .05))
    x1 = max(x1, int(img.size[0] * .95))

    x0 = max(0, x0 - 20)
    x1 = min(img.size[0], x1 + 10)
    y0 = max(0, y0 - 20)
    y1 = min(img.size[1], y1 + 10)
    img = img.crop((x0, y0, x1, y1))
    return img


def save_image(img):
    buffer = io.BytesIO()
    img.save(buffer, format="png", quality=95)
    return buffer


def mpl_make_table(html, dpi=100, figwidth=20, fontsize=23):
    df = html_to_df(html)
    height = df.shape[0] * 1
    fig = plt.Figure(dpi=dpi, figsize=(figwidth, height))
    ax = fig.add_subplot()

    for spine in ax.spines.values(): 
        spine.set_visible(False)

    ax.tick_params(length=0, labelsize=0)
    width = min(df.shape[1] * .13, 1)
    left  = (1 - width) / 2 + .03
    if left + width > .9:
        left = .05
        width = .95
        bbox_inches = 'tight'
        if len(df.columns) > 7:
            fontsize = 18
        else:
            fontsize = 20
    else:
        bbox_inches = None
    
    ax.set_position([left, 0, width, 1])
    wrap_width = 12 + max(0, 10 - df.shape[1]) // 2
    cellText = get_values(df, wrap_width)
    color_map = {0: ["#f5f5f5"] * df.shape[1], 
                  1: ["#ffffff"] * df.shape[1]}
    cellColours = [color_map[i % 2] for i in range(len(df))]
    rowColours = [c[0] for c in cellColours]
    colWidths = get_col_widths(df)
    rowLabels = [handle_decimal(str(val), True, wrap_width) for val in df.index.tolist()]
    colLabels = [handle_decimal(str(val), True, wrap_width) for val in df.columns.tolist()]
    t = ax.table(cellText=cellText, 
                 cellColours=cellColours,
                 colWidths=colWidths,
                 colLabels=colLabels,
                 colLoc='right',
                 rowLabels=rowLabels, 
                 rowColours=rowColours,
                 bbox=[0, 0, 1, 1])
    t.auto_set_font_size(False)
    t.set_fontsize(fontsize)
    for key, cell in t.get_celld().items():
        cell.set_linewidth(0)
        cell.set_text_props(fontfamily="Helvetica Neue")
        if key[0] == 0:
            cell.set_text_props(size=fontsize * 1, weight='bold')
    
    buffer = io.BytesIO()
    fig.savefig(buffer, bbox_inches=bbox_inches)
    img = crop_image(buffer)
    buffer = save_image(img)
    return base64.b64encode(buffer.getvalue()).decode()
