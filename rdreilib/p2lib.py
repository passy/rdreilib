# -*- coding: utf-8 -*-
"""
 rdreilib.p2lib
 ~~~~~~~~~~~~~~~~
 Passy2 numeric conversion library.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

import re, math, string

class P2Mixin(object):
    """This mixin allows to dynamically create a p2id property based on the
    current pk."""
    @property
    def p2id(self):
        return int_to_p2(self.id)

def int_to_p2(num):
    ret = []
    while num > 0:
        d = num%63
        if d < 10:
            ret.append(string.digits[d])
        elif d < 36:
            ret.append(string.ascii_lowercase[d-10])
        elif d < 62:
            ret.append(string.ascii_uppercase[d-36])
        else:
            ret.append('-')
        num //= 63
    ret.reverse()
    return "".join(ret)

def p2_to_int(num):
    res = 0
    num = str(num)
    for digit in num:
        res *= 63
        if digit in string.digits:
            res += int(digit)
        elif digit in string.ascii_lowercase:
            res += ord(digit)-ord('a')+10
        elif digit in string.ascii_uppercase:
            res += ord(digit)-ord('A')+36
        elif digit == '-':
            res += 62
        else:
            raise ValueError("Invalid character")
    return res
