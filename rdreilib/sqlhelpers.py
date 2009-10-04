# -*- coding: utf-8 -*-
"""
 rdreilib.sqlhelpers
 ~~~~~~~~~~~~~~~~~~~
 Additional helpers for using models and SQL.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

import logging
from werkzeug.exceptions import BadRequest

log = logging.getLogger("sqlhelpers")

def parse_filter_string(str, model, allowed=None, mappings=None):
    """Parses a query string in form of 'year:2008,comment:like%20my%20old'
    and returns a args-like list to pass it to filter().
    :param str {string}: The query string to parse.
    :param allowed {list}: Optional. A list of allowed columns to filter.
    :param mappings {dict}: Optional. A dict of keys mapped with their
    comparison operators like: {'name': 'contains', 'year': "__equal__"}
    Default operator for unmapped keys is ilike.
    :raises TypeError: if an argument of str is not in allowed and allowed
    is not None.
    """
    # TODO: Allow special filters like between for integer ranges.
    CMP_FALLBACK = 'contains'
    args = list()

    for bit in str.split(','):
        try:
            key, value = bit.split(":")
        except ValueError:
            continue
        if len(value) < 2:
            continue
        
        # Check whether it's allowed.
        if allowed and key not in allowed:
            raise TypeError("Filtering by key %s is is disallowed." % key)
        
        if not hasattr(model, key):
            raise TypeError("Filtering by this column is impossible. (;")

        # Get comparison operator.
        _cmp = mappings and mappings.get(key, CMP_FALLBACK) or \
                CMP_FALLBACK
        cmp = getattr(getattr(model, key), _cmp)
        
        # Build the filter. We really need a non-unicode string here.
        args.append(cmp(value))

    return args

def get_filter_values(filter_str):
    """Returns the values a filter is applied on."""
    
    try:
        return [bit.split(":")[1] for bit in filter_str.split(",") if
                bit.split(":")[1]]
    except IndexError:
        # We could check ':' in ... but this would not get errors if 
        # there is a value on one site only. Dunno if this affects
        # performance.
        return []
        

def parse_order(order_by, model, allowed = None, sort_key = None):
    """Returns a SQLAlchemy expression.
    @param order_by {string}: A single string value like u'-year'
    @param model {class}: The model that's going to be sorted.
    @param allowed {list}: Optional. A list containing allowed columns.
    @param sort_key {reference}: Is set to the order without leading -
    @raises BadRequest if sorting column is not in allowed.
    """
    
    sort_key = (order_by[0] == '-') and order_by[1:] or order_by
    if allowed is not None and \
       sort_key not in allowed:
        raise BadRequest("Unsupported sorting column!")
    
    try:    
        field = getattr(model, sort_key)
    except AttributeError:
        log.warn("Sorting by field %s requested that does not exist!", sort_key)
        return list()
        
    if order_by[0] == '-':
        return field.desc()
    else:
        return field.asc()
        
