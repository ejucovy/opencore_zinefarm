from zine._core import _create_zine
import os.path

from zine.application import Zine

from zine.opencoreglue import CustomRequestApp

class ZineFarm(object):
    def __call__(self, environ, start_response):
        project = environ.get('HTTP_X_OPENPLANS_PROJECT')
        if not project: 
            raise RuntimeError("wtf mate")
        zine_data_base = '/tmp/zinefarm'
        instance_folder = os.path.join(
            zine_data_base, project)
        app = object.__new__(CustomRequestApp)
        from zine import _core
        _core._application = app
        app.__init__(instance_folder)
        return app(environ, start_response)

def app_factory(*args, **kw):
    return ZineFarm()
