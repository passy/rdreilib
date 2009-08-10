# -*- coding: utf-8 -*-
"""
 rdreilib.sidebar
 ~~~~~~~~~~~~~~~~
 Datastructures for sidebar modules.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL, see doc/LICENSE for more details.
 """

from glashammer.utils.wrappers import render_template
from p2lib import p2_to_int
from jsonlib import JSONException

import re, logging, types

log = logging.getLogger("rdreilib.sidebar")

RE_SIMPLE_MODULECALL = re.compile("(?P<name>[A-Za-z0-9_]+)\((?P<key>[A-Za-z0-9_]+)=(?P<value>[^)]+)\)")
RE_COMPLEX_MODULECALL_OUTER = re.compile("(?P<name>[A-Za-z0-9_]+)\((?P<inner>[^)]+)\)")

class PermissionError(Exception):
    pass

class SidebarModule(object):
    name = str()
    target_id = str()
    target_class = str()
    init_cmd = str()
    meta = dict()
    extra = dict()
    
    template = str()
    #: Sets whether extra kwargs are accepted or not.
    accept_extra = False
    
    def __init__(self, request, extra=None):
        self.request = request
        self._set_defaults()
        self.populate_meta()

        if self.accept_extra:
            self.extra = extra
        
        # Could be usefull
        self.meta['template'] = self.template
        
    def _set_defaults(self):
        raise NotImplementedError()

    @classmethod
    def request_module(cls, name, request, *args, **kwargs):
        """Trys to find the requested module by its name and returns
        the module as dict or raises an LookupError if the module
        was not found."""

        # Parse the name
        pname = cls._parse_name(name)

        if type(pname) in types.StringTypes:
            sm_class = cls.get_class(name)
        elif type(pname) == type(None):
            # The parser usually does not raise exceptions, but rather return
            # NoneType.
            raise ValueError("Malformed module load string!")
        else:
            # Let's hope it's an array. (;
            log.debug("Loading probably parameterized module %r." % pname)
            sm_class = cls.get_class(pname[0])
            if not sm_class.accept_extra:
                # Don't tell those script kiddies too much.
                raise LookupError()
            kwargs['extra'] = pname[1]

        sm = sm_class(request, *args, **kwargs)

        if sm.has_permission():
            return sm.to_dict()
        else:
            raise PermissionError("The module %r does not want to be loaded." % name)

    @staticmethod
    def _parse_name(name):
        """Seperates the module name from it keyword arguments.
        >>> _parse_name("assign_course(student_id=5, name=Bert)")
        ['assign_course', {'student_id': 5, 'name': 'Bert'}]
        >>> _parse_name("this_is(notvalid)")
        None
        """
        if '(' in name and ')' in name:
            if "," in name:
                # More than one pair
                match1 = RE_COMPLEX_MODULECALL_OUTER.match(name)
                if not match1:
                    log.debug("_parse_name: Syntax error at outer level.")
                    return None

                rname = match1.group("name")
                kwargs = dict()
                for pair in [p.strip() for p in \
                             match1.group("inner").split(',')]:
                    try:
                        bits = pair.split('=')
                    except ValueError:
                        log.debug("_parse_name: Syntax error at equation level.")
                        return None
                    kwargs[bits[0]] = bits[1]
                return [rname, kwargs]
            else:
                log.debug("Did not find ',' in %r", name)
                # Only one pair
                match = RE_SIMPLE_MODULECALL.match(name)
                if not match:
                    # Malformed string!
                    log.debug("_parse_name: Syntax error at simple parsing.")
                    return None
                return [match.group(1), {match.group(2): match.group(3)}]
        else:
            return name
    
    @classmethod
    def get_class(cls, name):
        sm_class = None
        for mod in cls.__subclasses__():
            if mod.name == name:
                sm_class = mod
                break
        if not sm_class:
            raise LookupError("Unsupported module %r requested" % name)
        return sm_class
        
    def has_permission(self):
        """Checks if this module may be loaded. This is not automatically respected
        by render() or to_dict(). You need to check this yourself!"""
        return True
    
    def populate_meta(self):
        "Implement this method to add some dynamic data to self.meta"
        pass
    
    def render(self, path, dictionary):
        return render_template(path, **dictionary)
        
    def to_dict(self):
        return {'name': self.name,
                'target_id': self.target_id,
                'target_class': self.target_class,
                'init_cmd': self.init_cmd,
                'meta': self.meta,
                'html': self.render()}

    def _get_extra_instance(self, model, key, user_attr="creation_user"):
        """Tries to get a instance of model with getp2. The primary key is
        obtained from the extra key ``key``.
        @param model {class}: A sqlalchemy model class with a query attribute.
        @param key {string}: The extra key where to find the pk id.
        @param user_attr {string}: Check for user attribute (default:
            "creation_user") match with req.user or do nothing if None.
        """
        try:
            id_ = p2_to_int(self.extra[key])
        except (ValueError, KeyError, TypeError):
            # Pretend the module does not exist (with these parameters)
            raise LookupError("No compatible module found for these "
                              "parameters.")

        instance = model.query.get(id_)
        if not instance:
            raise JSONException("Could not find an instance of what you are "
                                "searching for.")
        if user_attr:
            attr = getattr(instance, user_attr) 
            if attr != self.request.user:
                raise PermissionError("You are not authorized to view and/or "
                                      "alter this instance.")
        return instance

