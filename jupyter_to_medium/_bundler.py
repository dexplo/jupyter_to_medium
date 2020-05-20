import io
import os
import nbformat

def _jupyter_bundlerextension_paths():
    """Declare bundler extensions provided by this package."""
    return [{
        # unique bundler name
        "name": "jupyter_to_mediu_bundler",
        # module containing bundle function
        "module_name": "_bundler",
        # human-readable menu item label
        "label" : "Publish as Medium post and download Markdown",
        # group under 'deploy' or 'download' menu
        "group" : "deploy",
    }]


def bundle(handler, model):
    """Create a compressed tarball containing the notebook document.

    Parameters
    ----------
    handler : tornado.web.RequestHandler
        Handler that serviced the bundle request
    model : dict
        Notebook model from the configured ContentManager
    """
    filename = model['name']
    nb = model['content']
    path = model['path']

    filename_md = filename + '_medium' + '.md'

    # Set headers to trigger browser download
    handler.set_header('Content-Disposition', f'attachment; filename="{filename_md}"')
    handler.set_header('Content-Type', 'text/html')

    # Return the buffer value as the response
    handler.finish()