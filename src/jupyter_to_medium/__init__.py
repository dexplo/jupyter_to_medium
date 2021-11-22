from jupyter_to_medium._publish_to_medium import publish


def _jupyter_nbextension_paths():
    return [
        dict(
            section="notebook",
            src="nbextension",
            dest="jupyter_to_medium",
            require="jupyter_to_medium/index",
        )
    ]
