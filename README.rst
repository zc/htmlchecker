HTML/DOM Checker
================

When testing code (like widgets) that generates DOM nodes, we want to
be able to make assertions about what matters. Examples of things we'd
like to ignore:

- attribute order
- extra attributes
- attribute order
- extra classes
- extra nodes

zc.htmlchecker provides a checker object that can be used by itself,
or as a doctest output checker.

.. contents::

Getting started
---------------

Let's look at some examples.

Here's a sample expected string::

    <body>
      <button class="mybutton">press me</button>
    </body>

.. -> expected

Let's create a checker:

    >>> import zc.htmlchecker
    >>> checker = zc.htmlchecker.HTMLChecker()

You can call its check method with expected and observed HTML:

    >>> checker.check(
    ... expected,
    ... """<html><body><button x='1' class="widget mybutton">press me</button>
    ...          </body></html>""")

If there's a match, then nothing is returned.  For there to be a
match, the expected output merely has to be unambiguously found in the
observed output. In the above example, there was a single body tag,
so it knew how to do the match.  Note that whitespace differences were
ignored, as were extra observed attributes and an extra class.

doctest Checker
---------------

To use ``zc.htmlchecker`` as a doctest checker, pass an instance of
``HTMLChecker`` as an output checker when setting up your doctests.

.. low-level doctest checker tests

    When used as a doctest output checker, its ``check_output`` method
    returns a boolean indicating whether there was a match:

        >>> checker.check_output(
        ... expected,
        ... """<html><body><button x='1' class="mybutton">press me</button>
        ...          </body></html>""", 0)
        True

    And the ``output_difference`` shows differences. It's a little weird
    (not our fault) in that it takes an example, rather than a wanted
    text:

        >>> class Example:
        ...    def __init__(self, want): self.want = want
        >>> checker.output_difference(
        ... Example(expected),
        ... """<html><body><button x='1' class="mybutton">press me</button>
        ...          </body></html>""", 0)
        ''

    Now let's make it fail:

        >>> checker.check(
        ... expected,
        ... """<html><body><button x='1' class="button">press me</button>
        ...          </body></html>""")
        Traceback (most recent call last):
        ...
        MatchError: missing class: mybutton
        Expected:
        <button class="mybutton">
         press me
        </button>
        <BLANKLINE>
        Observed:
        <button class="button" x="1">
         press me
        </button>
        <BLANKLINE>

        >>> checker.check_output(
        ... expected,
        ... """<html><body><button x='1' class="button">press me</button>
        ...          </body></html>""", 0)
        False

        >>> print checker.output_difference(
        ... Example(expected),
        ... """<html><body><button x='1' class="button">press me</button>
        ...          </body></html>""", 0),
        missing class: mybutton
        Expected:
        <button class="mybutton">
         press me
        </button>
        <BLANKLINE>
        Observed:
        <button class="button" x="1">
         press me
        </button>

When used as a doctest checker, expected text that doesn't start with
``<`` is checked with the default checker, or a checker you pass in as
base.

.. test above

    >>> checker.check_output('1', '2', 0)
    False

    >>> import doctest
    >>> checker.check_output('1...3', '123', doctest.ELLIPSIS)
    True

    >>> class FooChecker:
    ...     def check_output(self, want, got, flags):
    ...         return 'foo' in got.lower()

    >>> checker2 = zc.htmlchecker.HTMLChecker(FooChecker())
    >>> checker2.check_output('1', '2 foo', 0)
    True
    >>> checker2.check_output('<a>', '2 foo', 0)
    False

You may want to have some html examples checked with another
checker. In that case, you can specify a prefix.  Only examples that
begin with the prefix will be checked with the HTML checker, and the
prefix will be removed.

.. test above

    >>> checker2 = zc.htmlchecker.HTMLChecker(FooChecker(), prefix="<>")
    >>> checker2.check_output('<a></a>', '2 foo', 0)
    True
    >>> checker2.check_output('<><a></a>', '2 foo', 0)
    False
    >>> checker2.check_output('<><a></a>', '<a></a>', 0)
    True

    >>> checker3 = zc.htmlchecker.HTMLChecker(prefix="<>")
    >>> checker3.check_output('<><a></a>', '<b><a></a></b>', 0)
    True
    >>> checker3.check_output('<a></a>', '<b><a></a></b>', 0)
    False

    >>> print checker3.output_difference(Example('<a></a>'), '<c></c>', 0)
    Expected:
        <a></a>Got:
        <c></c>

    >>> print checker3.output_difference(Example('<><a></a>'), '<c></c>', 0)
    Couldn't find wildcard match
    Expected:
    <a>
    </a>
    Observed:
    <c>
    </c>

Expecting multiple nodes
------------------------

We can expect more than a single node::

    <button>Cancel</button>
    <button>Save</button>

.. -> expected

This example expects 2 button nodes somewhere in the output.

    >>> checker.check(expected,
    ... """<html><body>
    ...         <button id='cancel_button' class="button">Cancel</button>
    ...         <button id='save_button' class="button">Save</button>
    ...    </body></html>""")

But if there isn't a match, it can be harder to figure out what's
wrong:

    >>> checker.check(expected,
    ... """<html><body>
    ...         <button id='cancel_button' class="button">Cancel</button>
    ...         <button id='save_button' class="button">OK</button>
    ...    </body></html>""")
    Traceback (most recent call last):
    ...
    MatchError: Couldn't find wildcard match
    Expected:
    <button>
     Save
    </button>
    <BLANKLINE>
    Observed:
    <html>
     <body>
      <button class="button" id="cancel_button">
       Cancel
      </button>
      <button class="button" id="save_button">
       OK
      </button>
     </body>
    </html>

We'll come back to wild card matches in a bit.  Here, the matcher
detected that it didn't match a button, but couldn't be specific about
which button was the problem.  We can make its job easier using ids::

    <button id='cancel_button'>Cancel</button>
    <button id='save_button'>Save</button>

.. -> expected

Now we're looking for button nodes with specific ids.

    >>> checker.check(expected,
    ... """<html><body>
    ...         <button id='cancel_button' class="button">Cancel</button>
    ...         <button id='save_button' class="button">OK</button>
    ...    </body></html>""")
    Traceback (most recent call last):
    ...
    MatchError: text nodes differ u'Save' != u'OK'
    Expected:
    <button id="save_button">
     Save
    </button>
    <BLANKLINE>
    Observed:
    <button class="button" id="save_button">
     OK
    </button>
    <BLANKLINE>

That's a lot more helpful.

Wildcards
---------

Speaking of wild card matches, sometimes you want to ignore
intermediate nodes.  You can do this by using an ellipsis at the top of
a node that has intermediate nodes you want to ignore::

  <form>
    ...
    <button id='cancel_button'>Cancel</button>
    <button id='save_button'>Save</button>
  </form>

.. -> expected

In this case, we want to find button nodes inside a form node. We
don't care if there are intermediate nodes.

    >>> checker.check(expected,
    ... """<html><body>
    ...    <form>
    ...      <div>
    ...         <button id='cancel_button' class="button">Cancel</button>
    ...         <button id='save_button' class="button">Save</button>
    ...      </div>
    ...    </form>
    ...    </body></html>""")

When looking for expected text, we basically do a wild-card match on
the observed text.

Sometimes, we want to check for text nodes that may be embedded in
some generated construct that we can't control (like a grid produced
by a library).  To do that, include a text node that starts with a
line containing an ellipsis. For example, we may expect a grid/table
with some data::

   <div id="mygrid" name="">
   ...
   Name    Favorite Color
   Sally   Red
   Bill    Blue
   </div>

.. -> expected

We don't know exactly how our library is going to wrap the data, so we
just test for the presense of the data.

    >>> import sys
    >>> try: checker.check(expected,
    ... """<html><body>
    ...      <div id='mygrid' name='' xid="1">
    ...        <table>
    ...          <tr><th>Name</th><th>Favorite Color</th></tr>
    ...          <tr><td>Sally</td><td>Red  </td></tr>
    ...          <tr><td>Bill </td><td>Green</td></tr>
    ...        </table>
    ...      </div>
    ...    </body></html>""")
    ... except zc.htmlchecker.MatchError:
    ...    error = sys.exc_info()[1]
    ... else: print 'oops'
    >>> print error # doctest: +ELLIPSIS
    Blue not found in text content.
    ...

    >>> checker.check(expected,
    ... """<html><body>
    ...      <div id='mygrid' name='' xid="1">
    ...        <table>
    ...          <tr><th>Name</th><th>Favorite Color</th></tr>
    ...          <tr><td>Sally</td><td>Red  </td></tr>
    ...          <tr><td>Bill </td><td>Blue</td></tr>
    ...        </table>
    ...      </div>
    ...    </body></html>""")





You can use other BeautifulSoup parsers
---------------------------------------

HTMLChecker uses BeautifulSoup.  It uses the ``'html5lib'`` parser by
default, but you can pass a different parser name.  You probably want
to stere clear of the ``'html.parser'`` parser, as it's buggy:

    >>> checker = zc.htmlchecker.HTMLChecker(parser='html.parser')
    >>> checker.check('<input id="x">', '<input id="x"><input>')
    Traceback (most recent call last):
    ...
    MatchError: Wrong number of children 1!=0
    Expected:
    <input id="x"/>
    <BLANKLINE>
    Observed:
    <input id="x">
     <input/>
    </input>

Here, ``'html.parser'`` decided that the input tags needed closing
tags, even though the HTML input tag is empty.  This is likely in part
because the underlying parser is an XHTML parser.

Changes
=======

0.1.0 2013-08-31
----------------

Initial release.
