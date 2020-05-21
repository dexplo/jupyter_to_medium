from pathlib import Path

from tornado import gen

from ._publish_to_medium import publish


def _jupyter_bundlerextension_paths():
    return [{
        "name": "jupyter_to_medium_bundler",
        "module_name": "jupyter_to_medium._bundler",
        "label" : "Medium Post",
        "group" : "deploy",
    }]


def get_html(xsrf_input, title):
    html = f'''
    <h1>Publish your Jupyter Notebook to Medium</h1>

    <form method="GET">
    {xsrf_input}

    <h3>Integration token</h3>
    <p>You may leave this field blank if your integration token is located in your home 
       directory at '.jupyter_to_medium/integration_token'. If you don't have an integration 
       token, <a href="https://github.com/Medium/medium-api-docs">learn how to request one 
        from Medium.</a>
    </p>
    <input type="text" id="integration_token" name="integration_token"><br><br>
    
    <h3>Title</h3>
    <input type="text" id="title" name="title" value="{title}"><br><br>

    <h3>Publication Name</h3>
    <input type="text" id="pub_name" name="pub_name"><br><br>

    <h3>Tags</h3>
    <p>Separate each tag with a comma. Max of 5</p>
    <input type="text" id="tags" name="tags"><br><br>
    
    <h3>Publish Status</h3>
    <div style="display: flex">
        <label for="draft">Draft</label><br>
        <input type="radio" id="draft" name="publish_status" value="draft" checked = "checked">
        
        <label for="public">Public</label><br>
        <input type="radio" id="public" name="publish_status" value="public">

        <label for="unlisted">Unlisted</label><br>
        <input type="radio" id="unlisted" name="publish_status" value="unlisted">
    </div>

    <h3>Notify Followers</h3>
    <div style="display: flex">
        <label for="no">No</label><br>
        <input type="radio" id="no" name="notify_followers" value="False" checked = "checked">
        
        <label for="yes">Yes</label><br>
        <input type="radio" id="yes" name="notify_followers" value="True">
    </div>

    <h3>License</h3>
    <select id="license" name="license">
        <option value="all-rights-reserved">All Rights Reserved</option>
        <option value="cc-40-by">cc-40-by</option>
        <option value="cc-40-by-sa">cc-40-by-sa</option>
        <option value="cc-40-by-nd">cc-40-by-nd</option>
        <option value="cc-40-by-nc">cc-40-by-nc</option>
        <option value="cc-40-by-nc-nd">cc-40-by-nc-nd</option>
        <option value="cc-40-by-nc-sa">cc-40-by-nc-sa</option>
        <option value="cc-40-zero">cc-40-zero</option>
        <option value="public-domain">public-domain</option>
    </select>
    
    <h3>Canonical URL</h3>
    <input type="text" id="canonical_url" name="canonical_url"><br><br>

    <input type="hidden" name="bundler" value="jupyter_to_medium_bundler">
    <input type="submit" value="Publish">
    </form>
    '''
    return html

def upload(model, handler):
    arguments = ['title', 'integration_token', 'pub_name', 'tags', 
                'publish_status', 'notify_followers', 'license', 'canonical_url']

    kwargs = {arg: handler.get_query_argument(arg) for arg in arguments}
    path = model['path']
    kwargs['filename'] = path
    kwargs['integration_token'] = kwargs['integration_token'] or None
    kwargs['pub_name'] == kwargs['pub_name'] or None
    kwargs['tags'] = kwargs['tags'].split(',')[:5]
    kwargs['notify_followers'] = bool(kwargs['notify_followers'])
    kwargs['canonical_url'] = kwargs['canonical_url'] or None

    json_data = publish(**kwargs)
    return json_data

def success(handler, json_data):
    url = json_data['data']['url']
    title = json_data['data']['title']
    html = f'''
    <h1>Published to Medium!</h1>
    <a href="{url}">Link to your Medium Post: {title}</a>
    '''
    handler.write(html)
    
@gen.coroutine
def bundle(handler, model):
    """
    Parameters
    ----------
    handler : tornado.web.RequestHandler
        Handler that serviced the bundle request
    model : dict
        Notebook model from the configured ContentManager
    """
    title = handler.get_query_argument('title', None)
    notebook_filename = Path(model['name']).stem
    xsrf_input = handler.xsrf_form_html()
    html = get_html(xsrf_input, notebook_filename)
    if title is None:
        handler.write(html)
    else:
        handler.write('Publishing to Medium...')
        handler.flush()
        json_data = upload(model, handler)
        success(handler, json_data)
  
    print(handler.request)
    handler.finish()