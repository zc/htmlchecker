HTML/DOM Checker
================

When testing code (like widgets) that generates DOM nodes, we want to
be able to make assertions about what matters. Examples of things we'd
like to ignore:

- attribute order
- extra attributes
- extra classes
- extra nodes

zc.htmlchecker provides a checker object that can be used by itself,
or as a doctest output checker.

Let's look at some examples.

Here's a sample expected string::

    <body>
      <button class="mybutton">press me</button>
    </body>

.. -> expected

Let's create a checker:

    >>> import zc.htmlchecker
    >>> checker = zc.htmlchecker.HTMLChecker()

You can call it's check method with expected and observed HTML:

    >>> checker.check(
    ... expected,
    ... """<html><body><button x='1' class="widget mybutton">press me</button>
    ...          </body></html>""")

If there's a match, then nothing is returned.  For there to ba a
match, the expected output merely has to be unambiguously found in the
observed output. In the above example, there was a single body tag,
so it knew how to do the match.  Note that whitespace differences were
ignored, as were extra observerd attributes and an extra class.

When used as a doctest output checker, it's ``check_output`` method
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

We can expect more than a single node::

    <button>Cancel</button>
    <button>Save</button>

.. -> expected

This example expects 2 button nodes somewhere in the output.

    >>> checker.check(
    ... expected,
    ... """<html><body>
    ...         <button id='cancel_button' class="button">Cancel</button>
    ...         <button id='save_button' class="button">Save</button>
    ...    </body></html>""")

But if there isn't a match, it can be harder to figure out what's
wrong:

    >>> checker.check(
    ... expected,
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

We'll come back to wild card matches in a second.  Here, the matcher
detected that it didn't match a button, but couldn't be specific about
which button was the problem.  We can make its job easier using ids::

    <button id='cancel_button'>Cancel</button>
    <button id='save_button'>Save</button>

.. -> expected

Now we're looking for button odes with specific ids.

    >>> checker.check(
    ... expected,
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

Speaking of wild card matches, sometimes you want to ignore
intermediate nodes.  You can do this by using an elipsis at the top of
a node that has intermediate nodes you want to ignore::

  <form>
    ...
    <button id='cancel_button'>Cancel</button>
    <button id='save_button'>Save</button>
  </form>

.. -> expected

In this case, we want to find button nodes inside a form node. We
don't care if there are intermediate nodes.

    >>> checker.check(
    ... expected,
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

When used as a doctest checker, expected text that doesn't start with
``<`` is checked with the default checker, or a checker you pass in a
s base:

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
checker. In that case, you can specify a prefix.  Only examples tyhat
befin with the prefix will be checked with the HTML checker, and the
prefix will be removed.  For example::

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
