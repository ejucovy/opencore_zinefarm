from zine._core import _create_zine
import os.path

from opencore_zinefarm.opencoreglue import CustomRequestApp
import webob.exc 
class ZineFarm(object):
    def __init__(self, zine_instances_directory,
                 shared_secret_filename,
                 admin_info_filename,
                 internal_root_url):
        self.zine_instances_directory = zine_instances_directory
        self.shared_secret_filename = shared_secret_filename
        self.admin_info_filename = admin_info_filename
        self.internal_root_url = internal_root_url

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

        # we use a copy of the environ because it's rude to modify 
        # the environ in place; something upstream of us might not
        # be expecting this injection
        environ_copy = environ.copy()

        # pass the shared_secret_filename through in the environment
        # so that the request object can find it when it needs to
        # authenticate the requesting user from a cookie
        environ_copy['OPENCORE_SECRET_FILENAME'] = self.shared_secret_filename

        # likewise pass the admin_info_filename through so that
        # zine can use site admin credentials to query projects'
        # security policies and memberhips (in case it's a closed
        # project)
        environ_copy['OPENCORE_ADMIN_INFO_FILENAME'] = self.admin_info_filename

        # and we pass the internal_root_url in the environ as well.
        # this is used to construct the url used when querying the
        # projects for their security policies and memberships
        environ_copy['OPENCORE_INTERNAL_ROOT_URL']  = self.internal_root_url

        return app(environ_copy, start_response)

def app_factory(global_conf,
                zine_instances_directory=None, 
                shared_secret_filename=None,
                admin_info_filename=None,
                internal_root_url=None,
                **kw):
    assert zine_instances_directory is not None, \
        "zine_instances_directory must be supplied"
    assert os.path.isdir(zine_instances_directory), \
        "zine_instances_directory `%s` does not exist" % zine_instances_directory
    assert shared_secret_filename is not None and os.path.isfile(shared_secret_filename), \
        "shared_secret_filename must be supplied and must be an existing file"
    assert admin_info_filename is not None and os.path.isfile(admin_info_filename), \
        "admin_info_filename must be supplied and must be an existing file"
    assert internal_root_url is not None, \
        "internal_root_url must be supplied"
    
    return ZineFarm(zine_instances_directory, 
                    shared_secret_filename,
                    admin_info_filename,
                    internal_root_url)
