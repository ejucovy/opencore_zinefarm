from zine._core import _create_zine
import os.path

from zine.application import Zine

from opencore_zinefarm.opencoreglue import CustomRequestApp
import webob.exc 
class ZineFarm(object):
    def __init__(self, zine_instances_directory):
        self.zine_instances_directory = zine_instances_directory
        self.shared_secret_filename = shared_secret_filename

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

        # pass the shared_secret_filename through in the environment
        # so that the request object can find it when it needs to
        # authenticate the requesting user from a cookie
        #
        # we use a copy of the environ because it's rude to modify 
        # the environ in place; something upstream of us might not
        # be expecting this injection
        environ_copy = environ.copy()
        environ_copy['OPENCORE_SECRET_FILENAME'] = self.shared_secret_filename

        return app(environ_copy, start_response)

def app_factory(zine_instances_directory=None, 
                shared_secret_filename=None,
                *args, **kw):
    assert zine_instances_directory is not None and os.path.isdir(zine_instances_directory), \
        "zine_instances_directory must be supplied and must be an existing directory"
    assert shared_secret_filename is not None and os.path.isfile(shared_secret_filename), \
        "shared_secret_filename must be supplied and must be an existing file"
    return ZineFarm(zine_instances_directory, shared_secret_filename)
