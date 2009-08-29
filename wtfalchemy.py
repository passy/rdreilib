# -*- coding: utf-8 -*-
"""
 wtforms.ext.sqlalchemy.orm
 ~~~~~~~~~~~~~~~~
 Tools for turning sqlalchemy declarative-style models into a form.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: Dual licensed under GPL v3 and MIT
 """

from wtforms import Form
from wtforms import fields as f
from wtforms import validators

# Actually we don't use this and it depends on a development version of wtforms,
# but this is still very useful!
#from wtforms.ext.sqlalchemy.fields import ModelSelectField

import logging
log = logging.getLogger('wtfalchemy')

class AdvancedDateTimeField(f.DateTimeField):
    """An advanced version of DateTimeField storing
    not parsable values in self.raw_value."""

    def process_formdata(self, valuelist):
        self.raw_data = None
        if valuelist and valuelist[0]:
            self.raw_data = valuelist[0]
        super(AdvancedDateTimeField, self).process_formdata(valuelist)

class SuperForm(Form):

    def __init__(self, *args, **kwargs):
        kwargs['idprefix'] = "id_"
        super(SuperForm, self).__init__(*args, **kwargs)

    def get_tcontext(self):
        # Get the fieldset definitions
        _fieldsets = ()
        if hasattr(self, 'Meta'):
            if hasattr(self.Meta, 'fieldsets'):
                _fieldsets = self.Meta.fieldsets
        
        if len(_fieldsets) == 0:
            _fieldsets = (
                (None, {'fields': [field[0] for field in self._fields]}),
            )
            
        
        context = []
        for name, options in _fieldsets:
            classes = options.get('classes', [])
            _context = {'name': name,
                        'classes': classes,
                        'collapse': 'collapse' in classes,
                        'fields': []}
            for fname in options.get('fields', []):
                if fname in self:
                    # Make required fields more obvious to the view
                    required = len(filter(lambda x: hasattr(x, 'func_name') and x.func_name == '_required' or getattr(x, 'field_flags', None) == ('required'), self[fname].validators)) == 1
                    setattr(self[fname], 'required', required)

                    _context['fields'].append(self[fname])
                else:
                    log.warn("Fieldsets field definition for %s references "\
                                  "non-existent field %s." % (name, fname))
            context.append(_context)
        
        return context

class ModelConverter(object):
    # This is basicly the same as in the django converter.
    # Order is from http://www.sqlalchemy.org/docs/05/reference/sqlalchemy/types.html
    SIMPLE_CONVERSIONS = {
        'String': f.TextField,
        'Unicode': f.TextField,
        'Text': f.TextAreaField,
        'UnicodeText': f.TextAreaField,
        'Integer': f.IntegerField,
        'SmallInteger': f.IntegerField,
        'Numeric': f.IntegerField, # Why is in ext.django.orm a list for this?
        'Float': f.TextField,
        'DateTime': f.DateTimeField,
        'Interval': f.IntegerField, # TODO
        'Boolean': f.BooleanField,
        'Binary': f.TextField, # TODO: Test
        'PickleType': f.TextField # TODO
    }

    def __init__(self, model):
        self.model = model

    def convert(self, column):
        kwargs = {
            'label': column.info.get('label', column.name),
            'description': column.description,
            'validators': [],
            'default': column.default and column.default.arg
        }
        
        if column.info.get('optional', False):
            kwargs['validators'].append(validators.optional())
        elif not column.nullable:
            kwargs['validators'].append(validators.required())
        
        if hasattr(column.type, 'length') and column.type.length is not None:
            kwargs['validators'].append(validators.length(max=column.type.length))
        
        fname = type(column.type).__name__

        if len(column.foreign_keys) > 0:
            return self.conv_ForeignKey(kwargs, column)

        if fname in self.SIMPLE_CONVERSIONS:
            return self.SIMPLE_CONVERSIONS[fname](**kwargs)
        else:
            mod = getattr(self, 'conv_%s' % fname, None)
            if mod is not None:
                return mod(kwargs, column)

    def _get_cls(self, tablename):
        matches = [v for v in self.model._decl_class_registry.values() if
                    v.__tablename__ == tablename]
        if matches:
            return matches.pop()

    # The datetime fields should be locale concious!

    def conv_ForeignKey(self, kwargs, column):
        # Dunno what happens on multiple ones.
        tablename = column.foreign_keys[0].column.table.name
        model = self._get_cls(tablename)

    def conv_Time(self, kwargs, column):
        return AdvancedDateTimeField(format="%H-%M-%S", **kwargs)

    def conv_Date(self, kwargs, column):
        return AdvancedDateTimeField(format=r"%d.%m.%Y", **kwargs)

def model_form(model, base_class=SuperForm, include_pk=False, exclude=None):
    """
    Create a WTForm for a given SQLAlchemy declarative-style model class::

        >>> from wtforms.ext.sqlalchemy.orm import model_form
        >>> from myproject.myapp.models import User
        >>> UserForm = model_form(User)

    The form can be made to extend your own form by passing the ``base_class``
    parameter. Primary key fields are not included unless you specify 
    ``include_pk=True``.
    Foreign Keys aren't handled yet.
    """
    
    meta = model._sa_class_manager.mapper
    f_dict = {}
    exclude = exclude or []
    converter = ModelConverter(model)
    for column in meta.c:
        if not include_pk and column.primary_key:
            continue
        if column.key in exclude:
            continue

        formfield = converter.convert(column)

        if formfield is not None:
            f_dict[column.name] = formfield
    
    return type(model.__name__ + "Form", (base_class, ), f_dict)

