"""
Python Markdown

A Python implementation of John Gruber's Markdown.

Documentation: https://python-markdown.github.io/
GitHub: https://github.com/Python-Markdown/markdown/
PyPI: https://pypi.org/project/Markdown/

Started by Manfred Stienstra (http://www.dwerg.net/).
Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
Currently maintained by Waylan Limberg (https://github.com/waylan),
Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

Copyright 2007-2018 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE.md for details).
"""

import os
import sys
import unittest
import textwrap
from . import markdown, Markdown, util

try:
    import tidylib
except ImportError:
    tidylib = None

__all__ = ['TestCase', 'LegacyTestCase', 'Kwargs']


class TestCase(unittest.TestCase):
    """
    A unittest.TestCase subclass with helpers for testing Markdown output.

    Define `default_kwargs` as a dict of keywords to pass to Markdown for each
    test. The defaults can be overridden on individual tests.

    The `assertMarkdownRenders` method accepts the source text, the expected
    output, and any keywords to pass to Markdown. The `default_kwargs` are used
    except where overridden by `kwargs`. The ouput and expected ouput are passed
    to `TestCase.assertMultiLineEqual`. An AssertionError is raised with a diff
    if the actual output does not equal the expected output.

    The `dedent` method is available to dedent triple-quoted strings if
    necessary.

    In all other respects, behaves as unittest.TestCase.
    """

    default_kwargs = {}

    def assertMarkdownRenders(self, source, expected, expected_attrs=None, **kwargs):
        """
        Test that source Markdown text renders to expected output with given keywords.

        `expected_attrs` accepts a dict. Each key should be the name of an attribute
        on the `Markdown` instance and the value should be the expected value after
        the source text is parsed by Markdown. After the expected output is tested,
        the expected value for each attribute is compared against the actual
        attribute of the `Markdown` instance using `TestCase.assertEqual`.
        """

        expected_attrs = expected_attrs or {}
        kws = self.default_kwargs.copy()
        kws.update(kwargs)
        md = Markdown(**kws)
        output = md.convert(source)
        self.assertMultiLineEqual(output, expected)
        for key, value in expected_attrs.items():
            self.assertEqual(getattr(md, key), value)

    def dedent(self, text):
        """
        Dedent text.
        """

        # TODO: If/when actual output ends with a newline, then use:
        # return textwrap.dedent(text.strip('/n'))
        return textwrap.dedent(text).strip()


class recursionlimit:
    """
    A context manager which temporarily modifies the Python recursion limit.

    The testing framework, coverage, etc. may add an arbitrary number of levels to the depth. To maintain consistency
    in the tests, the current stack depth is determined when called, then added to the provided limit.

    Example usage:

        with recursionlimit(20):
            # test code here

    See https://stackoverflow.com/a/50120316/866026
    """

    def __init__(self, limit):
        self.limit = util._get_stack_depth() + limit
        self.old_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(self.limit)

    def __exit__(self, type, value, tb):
        sys.setrecursionlimit(self.old_limit)


#########################
# Legacy Test Framework #
#########################


class Kwargs(dict):
    """ A dict like class for holding keyword arguments. """
    pass


def _normalize_whitespace(text):
    """ Normalize whitespace for a string of html using tidylib. """
    output, errors = tidylib.tidy_fragment(text, options={
        'drop_empty_paras': 0,
        'fix_backslash': 0,
        'fix_bad_comments': 0,
        'fix_uri': 0,
        'join_styles': 0,
        'lower_literals': 0,
        'merge_divs': 0,
        'output_xhtml': 1,
        'quote_ampersand': 0,
        'newline': 'LF'
    })
    return output


class LegacyTestMeta(type):
    def __new__(cls, name, bases, dct):

        def generate_test(infile, outfile, normalize, kwargs):
            def test(self):
                with open(infile, encoding="utf-8") as f:
                    input = f.read()
                with open(outfile, encoding="utf-8") as f:
                    # Normalize line endings
                    # (on Windows, git may have altered line endings).
                    expected = f.read().replace("\r\n", "\n")
                output = markdown(input, **kwargs)
                if tidylib and normalize:
                    try:
                        expected = _normalize_whitespace(expected)
                        output = _normalize_whitespace(output)
                    except OSError:
                        self.skipTest("Tidylib's c library not available.")
                elif normalize:
                    self.skipTest('Tidylib not available.')
                self.assertMultiLineEqual(output, expected)
            return test

        location = dct.get('location', '')
        exclude = dct.get('exclude', [])
        normalize = dct.get('normalize', False)
        input_ext = dct.get('input_ext', '.txt')
        output_ext = dct.get('output_ext', '.html')
        kwargs = dct.get('default_kwargs', Kwargs())

        if os.path.isdir(location):
            for file in os.listdir(location):
                infile = os.path.join(location, file)
                if os.path.isfile(infile):
                    tname, ext = os.path.splitext(file)
                    if ext == input_ext:
                        outfile = os.path.join(location, tname + output_ext)
                        tname = tname.replace(' ', '_').replace('-', '_')
                        kws = kwargs.copy()
                        if tname in dct:
                            kws.update(dct[tname])
                        test_name = 'test_%s' % tname
                        if tname not in exclude:
                            dct[test_name] = generate_test(infile, outfile, normalize, kws)
                        else:
                            dct[test_name] = unittest.skip('Excluded')(lambda: None)

        return type.__new__(cls, name, bases, dct)


class LegacyTestCase(unittest.TestCase, metaclass=LegacyTestMeta):
    """
    A `unittest.TestCase` subclass for running Markdown's legacy file-based tests.

    A subclass should define various properties which point to a directory of
    text-based test files and define various behaviors/defaults for those tests.
    The following properties are supported:

    location: A path to the directory fo test files. An absolute path is preferred.
    exclude: A list of tests to exclude. Each test name should comprise the filename
             without an extension.
    normalize: A boolean value indicating if the HTML should be normalized.
               Default: `False`.
    input_ext: A string containing the file extension of input files. Default: `.txt`.
    ouput_ext: A string containing the file extension of expected output files.
               Default: `html`.
    default_kwargs: A `Kwargs` instance which stores the default set of keyword
                    arguments for all test files in the directory.

    In addition, properties can be defined for each individual set of test files within
    the directory. The property should be given the name of the file without the file
    extension. Any spaces and dashes in the filename should be replaced with
    underscores. The value of the property should be a `Kwargs` instance which
    contains the keyword arguments that should be passed to `Markdown` for that
    test file. The keyword arguments will "update" the `default_kwargs`.

    When the class instance is created, it will walk the given directory and create
    a separate unitttest for each set of test files using the naming scheme:
    `test_filename`. One unittest will be run for each set of input and output files.
    """
    pass
