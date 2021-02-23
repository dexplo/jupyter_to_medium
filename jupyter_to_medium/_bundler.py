from pathlib import Path
import json
import urllib.parse

from tornado import gen

from ._publish_to_medium import publish


def _jupyter_bundlerextension_paths():
    return [{
        "name": "jupyter_to_medium_bundler",
        "module_name": "jupyter_to_medium._bundler",
        "label": "Medium Post",
        "group": "deploy",
    }]


def upload(model, handler):
    arguments = ['title', 'integration_token', 'pub_name', 'tags',
                 'publish_status', 'notify_followers', 'license', 'canonical_url',
                 'chrome_path', 'save_markdown', 'table_conversion', 'gistify',
                 'gist_threshold']

    kwargs = {arg: handler.get_query_argument(arg, None) for arg in arguments}
    path = model['path']
    kwargs['filename'] = path
    kwargs['integration_token'] = kwargs['integration_token'].strip() or None
    kwargs['pub_name'] == kwargs['pub_name'].strip() or None
    kwargs['tags'] = [tag.strip() for tag in kwargs['tags'].split(',')[:5]]
    kwargs['notify_followers'] = kwargs['notify_followers'] == "True"
    kwargs['canonical_url'] = kwargs['canonical_url'].strip() or None
    kwargs['save_markdown'] = kwargs['save_markdown'] == "True"
    kwargs['gistify'] = kwargs['gistify'] == "True"
    kwargs['gist_threshold'] = int(kwargs['gist_threshold'])

    # add these options in the future to html form
    # kwargs['chrome_path'] = kwargs['chrome_path'].strip() or None

    try:
        data = publish(**kwargs)
    except Exception as e:
        import traceback
        error_name = type(e).__name__
        error = f'{error_name}: {str(e)}'
        tb = traceback.format_exc()
        msg = error + f'\n\n{tb}'
        print(msg)
        msg = msg.replace('\n', '<br>')

        data = {'app_status': 'fail',
                'error_data': msg}
    else:
        if 'data' in data:
            data = data['data']
            data['app_status'] = "success"
        else:
            data = {'app_status': 'fail',
                    'error_data': 'Error: \n' + str(data)}

    return data


def read_html(name):
    mod_path = Path(__file__).parent
    html_path = mod_path / 'static' / f'{name}.html'
    return open(html_path).read()


def get_html_form(xsrf_input, title):
    html = read_html('form')
    return html.format(xsrf_input=xsrf_input, title=title)


def get_html_success(data):
    html = read_html('success')
    return html.format(**data)


def get_html_fail(data):
    error_data = data['error_data']
    error_message = json.dumps(error_data)
    html = read_html('fail')
    return html.format(error_message=error_message)


# synchoronous execution
def bundle(handler, model):
    """
    Parameters
    ----------
    handler : tornado.web.RequestHandler
        Handler that serviced the bundle request
    model : dict
        Notebook model from the configured ContentManager
    """
    app_status = handler.get_query_argument('app_status', None)

    if app_status is None:
        xsrf_input = handler.xsrf_form_html()
        notebook_filename = Path(model['name']).stem
        html = get_html_form(xsrf_input, notebook_filename)
        handler.write(html)
    elif app_status == 'waiting':
        html = read_html('waiting')
        handler.write(html)
        handler.flush()
        data = upload(model, handler)
        if data['app_status'] == 'success':
            html = get_html_success(data)
        else:
            html = get_html_fail(data)

        handler.write(html)

    handler.finish()
