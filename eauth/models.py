import sqlalchemy as db

from ..database import ModelBase
from sqlalchemy import orm
from glashammer.utils.local import get_app
from glashammer.bundles.sqlalchdb import metadata

from ..p2lib import int_to_p2

from hashlib import sha1
import datetime, types


class User(ModelBase):
    """Reasonably basic User definition. Probably would want additional
    attributes.
    """
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_name = db.Column(db.Unicode(50), unique=True)
    _password = db.Column('password', db.Unicode(40))

    is_staff = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)

    @property
    def user_p2id(self):
        return int_to_p2(self.user_id)

    def _set_password(self, password):
        """encrypts password on the fly."""
        self._password = self.__encrypt_password(password)

    def _get_password(self):
        """returns password"""
        return self._password

    password = orm.synonym('password', descriptor=property(_get_password,
                                                       _set_password))

    def __encrypt_password(self, password):
        """Hash the given password with SHA1."""
        
        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')

        else:
            password_8bit = password

        app = get_app()

        hashed_password = sha1()
        hashed_password.update(password_8bit)
        hashed_password.update(app.cfg['auth.secure_salt'])
        hashed_password = hashed_password.hexdigest()

        # make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode columns
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        return hashed_password

    def validate_password(self, password):
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param password: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: unicode object
        """
        return self.password == self.__encrypt_password(password)

    def is_authenticated(self):
        return True

    def has_perm(self, perm):
        "Returns True if the user has the specified permission."

        # If perm is a string, find the object.
        if type(perm) in types.StringTypes:
            _perm = Permission.query.filter_by(permission_name=perm).first()
            if not _perm:
                raise TypeError("Unknown permission %r!" % perm)
            perm = _perm

        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        # Iter through all the groups providing this permission.
        for group in perm.groups:
            if self in group.users:
                return True

        return False

    def has_perms(self, perm_list):
        "Returns True if the user has each of the specified permissions."
        for perm in perm_list:
            if not self.has_perm:
                return False
        return True

    def __unicode__(self):
        return u"<User[%d]('%s')>" % (self.user_id or "unsaved", self.user_name)

    def __repr__(self):
        return self.__unicode__()

class AnonymousUser(object):
    "Returned if not authenticated"

    user_id = 0
    user_name = None
    password = None
    user_p2id = 0

    is_staff = False
    is_active = False
    is_superuser = False

    validate_password = lambda self, password: False
    is_authenticated = lambda self: False

    def __repr__(self):
        return u"<AnonymousUser()>"


class Profile(ModelBase):
    """A one-to-one related table storing user related information.
    """
    __tablename__ = 'profile'

    #profile_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    security_question = db.Column(db.Unicode(120))
    # We store the answer in plain text. This is the usual way, because an
    # administrator could validate the answer by hand if something's going
    # wrong.
    security_answer = db.Column(db.Unicode(120))

    first_name = db.Column(db.Unicode(30), nullable=True)
    last_name = db.Column(db.Unicode(30), nullable=True)
    # Does a unique constraint work, if it's nullable?
    email = db.Column(db.Unicode(50), nullable=True)
    last_login = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, primary_key=True)
    user = orm.relation(User, backref='profile', uselist=False)

    def __init__(self):
        if not self.last_login:
            self.last_login = datetime.datetime.now()

# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = db.Table('group_permission', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = db.Table('user_group', metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    db.Column('group_id', db.Integer, db.ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# auth model

class Group(ModelBase):
    """An ultra-simple group definition.
    """
    __tablename__ = 'group'

    group_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    group_name = db.Column(db.Unicode(16), unique=True)
    users = orm.relation('User', secondary=user_group_table, backref='groups')

    def __init__(self, name):
        self.group_name = name

    def __unicode__(self):
        return "<Group[%d]('%s')>" % (self.group_id, self.group_name)

    def __repr__(self):
        return self.__unicode__()

class Permission(ModelBase):
    """A relationship that determines what each Group can do"""
    __tablename__ = 'permission'

    permission_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    permission_name = db.Column(db.Unicode(60), unique=True)
    groups = orm.relation(Group, secondary=group_permission_table,
                          backref='permissions')

    def __init__(self, name):
        self.permission_name = name

    def __unicode__(self):
        return "<Group[%d]('%s')>" % (self.permission_id, self.permission_name)

    def __repr__(self):
        return self.__unicode__()

