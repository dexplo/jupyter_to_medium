from ._publish_to_medium import publish
__version__ = '0.2.5'


def _jupyter_nbextension_paths():
    return [dict(
        section="notebook",
        src="nbextension",
        dest="jupyter_to_medium",
        require="jupyter_to_medium/index")]
