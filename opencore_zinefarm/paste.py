from zine._core import _create_zine
import os.path

from zine.application import Zine

from opencore_zinefarm.opencoreglue import CustomRequestApp
import webob.exc 
class ZineFarm(object):
    def __init__(self, zine_instances_directory):
        self.zine_instances_directory = zine_instances_directory

    def __call__(self, environ, start_response):
        # figure out which Zine instance to dispatch to
        # based on special request header
        project = environ.get('HTTP_X_OPENPLANS_PROJECT')
        if not project: 
            return webob.exc.HTTPNotFound("No blog found for project %s" % project)(environ, start_response)
        instance_folder = os.path.join(
            self.zine_instances_directory, project)

        # zine makes it very difficult to instantiate its wsgi app for some reason
        # you have to much around with another module's global
        # i'm not sure if this is safe, and it's certainly not kosher
        app = object.__new__(CustomRequestApp)
        from zine import _core
        _core._application = app
        app.__init__(instance_folder)

        return app(environ, start_response)

def app_factory(zine_instances_directory=None, *args, **kw):
    assert zine_instances_directory is not None and os.path.isdir(zine_instances_directory), \
        "zine_instances_directory must be supplied and must be an existing directory"
    return ZineFarm(zine_instances_directory)
