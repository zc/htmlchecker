##############################################################################
#
# Copyright (c) Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from bs4 import BeautifulSoup
import doctest
import re

class MatchError(Exception):

    def __str__(self):
        message, expected, observed = self.args
        out = []
        out.append(maybe_encode(message))
        out.append('Expected:')
        if not isinstance(expected, basestring):
            expected = expected.prettify()
        out.append(maybe_encode(expected))
        out.append('Observed:')
        if not isinstance(observed, basestring):
            observed = observed.prettify()
        out.append(maybe_encode(observed))
        return '\n'.join(out)

class HTMLChecker(doctest.OutputChecker):

    def __init__(self, base=None, prefix=None, parser='html5lib'):
        if base is None:
            base = doctest.OutputChecker()
        self.base = base
        self.prefix = prefix
        self.parser = parser

    def _bs(self, want):
        bs = BeautifulSoup(want, self.parser)
        if self.parser == 'html5lib':
            # html5lib adds body, head and html tags, which isn't what we want.
            want = want.lower()
            if '<body' not in want:
                bs.body.unwrap()
            if '<head' not in want:
                bs.head.decompose()
            if '<html' not in want:
                bs.html.unwrap()
        return bs

    def check(self, want, got):
        matches_(self._bs(got), self._bs(want), wild=True)

    def applicable(self, want):
        if self.prefix:
            if want.startswith(self.prefix):
                return want[len(self.prefix):]
        elif want.startswith('<'):
            return want

    def check_output(self, want, got, optionflags):
        expected = self.applicable(want)
        if not expected:
            return self.base.check_output(want, got, optionflags)

        try:
            self.check(expected, got)
        except MatchError:
            return False
        else:
            return True

    def output_difference(self, example, got, optionflags):
        expected = self.applicable(example.want)
        if not expected:
            return self.base.output_difference(example, got, optionflags)

        try:
            self.check(expected, got)
        except MatchError, v:
            return str(v)
        else:
            return ''


def maybe_encode(s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    return s

def beautifulText(node):
    if isinstance(node, unicode):
        return node
    if hasattr(node, 'name'):
        return u' '.join(beautifulText(c) for c in node)
    return ''

def matches_(observed, expected, wild=False):
    if getattr(expected, 'name', None) != getattr(observed, 'name', None):
        raise MatchError("tag names don't match", expected, observed)

    for name, e_val in expected.attrs.items():
        if not isinstance(e_val, basestring):
            e_val = ' '.join(e_val)

        o_val = observed.get(name)
        if o_val is None:
            raise MatchError("missing "+name, expected, observed)
        if not isinstance(o_val, basestring):
            o_val = ' '.join(o_val)

        if (e_val != o_val and not
            (re.match(r'^/.+/$', e_val) and re.match(e_val[1:-1], o_val))
            ):

            if name == 'class':
                oclasses = set(o_val.strip().split())
                for cname in e_val.strip().split():
                    if cname not in oclasses:
                        raise MatchError("missing class: "+cname,
                                             expected, observed)
            else:
                raise MatchError(
                    "attribute %s has different values: %r != %r"
                    % (name, e_val, o_val),
                    expected, observed)

    for enode in expected:
        if (not enode.name) and enode.strip().split('\n')[0] == '...':
            enode.replace_with(enode.split('...', 1)[1])
            wild = True
        break

    if wild:
        match_text = ''
        for enode in expected:
            if enode.name:
                if enode.get('id'):
                    onode = observed(id=enode['id'])
                    if not onode:
                        raise MatchError(
                            "In wildcard id search, couldn't find %r" %
                            enode['id'],
                            enode, observed)
                    matches_(onode[0], enode);
                else:
                    onodes = observed(enode.name)
                    for onode in onodes:
                        try:
                            matches_(onode, enode);
                        except MatchError:
                            if len(onodes) == 1:
                                raise # won't get a second chance, so be precise
                        else:
                            break
                    else:
                        raise MatchError(
                            "Couldn't find wildcard match", enode, observed)
            else:
                match_text += ' ' + enode.encode('utf8')

        match_text = match_text.strip()
        if match_text:
            text = beautifulText(observed)
            for token in match_text.split():
                try:
                    i = text.index(token)
                except ValueError:
                    raise MatchError(token + " not found in text content.",
                                         expected, observed)
                text = text[i+len(token):]
    else:
        enodes = [n for n in expected
                  if not isinstance(n, basestring) or n.strip()]
        onodes = [n for n in observed
                  if not isinstance(n, basestring) or n.strip()]
        if len(enodes) != len(onodes):
            raise MatchError(
                "Wrong number of children %r!=%r"
                % (len(onodes), len(enodes)),
                expected, observed)
        for enode, onode in zip(enodes, onodes):
            if enode.name or onode.name:
                matches_(onode, enode)
            else:
                e = beautifulText(enode).strip()
                o = beautifulText(onode).strip()
                if e != o:
                    raise MatchError(
                        'text nodes differ %r != %r' % (e, o),
                        expected, observed)
