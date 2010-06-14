from libopencore.query_project import get_users_for_project

from Cookie import BaseCookie
from zine.application import Request
from zine.models import User
import libopencore.auth

class OpencoreRequest(Request):
    def get_user(self):
        """
        Override core behavior by looking for user identification signed into
        OpenCore's __ac cookie rather than using the Zine session.
        """
        try:
            cookie = BaseCookie(
                self.environ['HTTP_COOKIE'])
            morsel = cookie['__ac']
        except KeyError:
            return User.query.get_nobody()

        secret_filename = self.environ['OPENCORE_SECRET_FILENAME']
        
        try:
            username, auth = libopencore.auth.authenticate_from_cookie(
                morsel.value, 
                libopencore.auth.get_secret(secret_filename))
        except:
            return User.query.get_nobody()

        username = username.lower()
        self.environ['REMOTE_USER'] = username
        user = User.query.filter_by(
            username=username).first()
        if user is None:
            # now create it
            user = User(username, 
                        'testy',
                        'ejucovy@gmail.com')
        return user

from zine.application import Zine

class CustomRequestApp(Zine):
    request_class = OpencoreRequest

from topp.utils import memorycache

#@memorycache.cache(120)
def find_role_for_user(username, project, environ):
    if username is None:
        return "Anonymous"

    admin_file = environ['OPENCORE_ADMIN_INFO_FILENAME']
    admin, password = libopencore.auth.get_admin_info(admin_file)
    domain = environ['OPENCORE_INTERNAL_ROOT_URL']

    users = get_users_for_project(project, domain, (admin, password))

    for user in users:
        name = user['username']
        if name != username: continue
        roles = user['roles']
        return roles[0]
    return "Authenticated"

from zine.database import users, user_privileges, privileges
from zine.privileges import BLOG_ADMIN
from zine.forms import EditUserForm
from zine.privileges import bind_privileges

def make_blogadmin(user):
    bind_privileges(user.own_privileges, ["BLOG_ADMIN"], user)

from zine.models import User, Group
def fixup_local_user_record(user, request):
    if len(Group.query.all()) == 0: setup_groups()

    if not user.is_somebody:
        return
    username = user.username
    if username is None:
        return

    role = find_role_for_user(username, 
                              request.environ['HTTP_X_OPENPLANS_PROJECT'],
                              request.environ)
    print role

    user = User.query.filter_by(username=username).first()

    remove_virtual_groups(user)

    group = Group.query.filter_by(name=role).first()

    user.groups.append(group)

def remove_virtual_groups(user):
    if not user.is_somebody:
        return

    for g in user.groups:
        if g.name != "BlogAdmin":
            user.groups.remove(g)

fix = fixup_local_user_record

from zine.database import init_database
from zine.api import db
from zine.config import Configuration
from zine.config import ConfigurationTransactionError
from zine.utils.crypto import gen_pwhash, gen_secret_key, new_iid
import os

def setup_groups():
    from zine.models import Group
    admin = Group(name="ProjectAdmin")
    manager = Group(name="BlogAdmin")
    member = Group(name="ProjectMember")
    auth = Group(name="Authenticated")
    from zine.privileges import DEFAULT_PRIVILEGES

    admin.privileges.add(DEFAULT_PRIVILEGES['BLOG_ADMIN'])

    member.privileges.add(DEFAULT_PRIVILEGES['CREATE_ENTRIES'])
    member.privileges.add(DEFAULT_PRIVILEGES['EDIT_OWN_ENTRIES'])
    member.privileges.add(DEFAULT_PRIVILEGES['EDIT_OTHER_ENTRIES'])
    member.privileges.add(DEFAULT_PRIVILEGES['ENTER_ADMIN_PANEL'])
    
    auth.privileges.add(DEFAULT_PRIVILEGES['ENTER_ADMIN_PANEL'])
    auth.privileges.add(DEFAULT_PRIVILEGES['CREATE_ENTRIES'])

def new_instance(database_uri, instance_folder, blog_url):
    e = db.create_engine(database_uri, 
                         instance_folder)
    init_database(e)

    config_filename = os.path.join(instance_folder, 
                                   'zine.ini')
    cfg = Configuration(config_filename)
    t = cfg.edit()
    t.update(
        maintenance_mode=False,
        blog_url=blog_url,
        secret_key=gen_secret_key(),
        database_uri=database_uri,
        language='en',
        iid=new_iid(),
        plugins='vessel_theme',
        theme='vessel'
        )
    #cfg._comments['[zine]'] = CONFIG_HEADER
    try:
        t.commit()
    except ConfigurationTransactionError:
        raise
        #error = _('The configuration file (%s) could not be opened '
        #          'for writing. Please adjust your permissions and '
        #          'try again.') % config_filename
    
