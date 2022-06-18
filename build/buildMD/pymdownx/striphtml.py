"""
Strip HTML (previously named Plain HTML).

pymdownx.striphtml
An extension for Python Markdown.
Strip classes, styles, and ids from html

MIT license.

Copyright (c) 2014 - 2017 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from markdown import Extension
from markdown.postprocessors import Postprocessor
import re


RE_TAG_HTML = re.compile(
    r'''(?x)
    (?:
        (?P<comments>(?:\r?\n?\s*)<!--(?:-(?!->)|[^-])*?-->(?:\s*)(?=\r?\n)|<!--[\s\S]*?-->)|
        (?P<scripts>
            (?P<script_open><(?P<script_name>style|script))
            (?P<script_attr>(?:\s+[\w\-:]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'`=<>]+))?)*)
            (?P<script_rest>\s*>.*?</(?P=script_name)\s*>)
        )|
        (?P<open><(?P<name>[\w\:\.\-]+))
        (?P<attr>(?:\s+[\w\-:]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'`=<>]+))?)*)
        (?P<close>\s*(?P<self_close>/)?>)|
        (?P<close_tag></(?P<close_name>[\w\:\.\-]+)\s*>)
    )
    ''',
    re.DOTALL | re.UNICODE
)

TAG_BAD_ATTR = r'''(?x)
(?P<attr>
    (?:
        \s+(?:%s)
        (?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'`=<>]+))
    )*
)
'''


class StripHtmlPostprocessor(Postprocessor):
    """Post processor to strip out unwanted content."""

    def __init__(self, strip_comments, strip_js_on_attributes, strip_attributes, md):
        """Initialize."""

        self.strip_comments = strip_comments
        self.re_attributes = None
        attributes = [re.escape(a.strip()) for a in strip_attributes]
        if strip_js_on_attributes:
            attributes.append(r'on[\w]+')
        if attributes:
            self.re_attributes = re.compile(
                TAG_BAD_ATTR % '|'.join(attributes),
                re.DOTALL | re.UNICODE
            )

        super(StripHtmlPostprocessor, self).__init__(md)

    def repl(self, m):
        """Replace comments and unwanted attributes."""

        if m.group('comments'):
            tag = '' if self.strip_comments else m.group('comments')
        else:
            if m.group('scripts'):
                tag = m.group('script_open')
                if self.re_attributes is not None:
                    tag += self.re_attributes.sub('', m.group('script_attr'))
                else:
                    tag += m.group('script_attr')
                tag += m.group('script_rest')
            elif m.group('close_tag'):
                tag = m.group(0)
            else:
                tag = m.group('open')
                if self.re_attributes is not None:
                    tag += self.re_attributes.sub('', m.group('attr'))
                else:
                    tag += m.group('attr')
                tag += m.group('close')
        return tag

    def run(self, text):
        """Strip out ids and classes for a simplified HTML output."""

        strip = self.strip_comments or self.strip_js_on_attributes or self.re_attributes
        return RE_TAG_HTML.sub(self.repl, text) if strip else text


class StripHtmlExtension(Extension):
    """StripHTML extension."""

    def __init__(self, *args, **kwargs):
        """Initialize."""

        self.config = {
            'strip_comments': [
                True,
                "Strip HTML comments at the end of processing. "
                "- Default: True"
            ],
            'strip_attributes': [
                [],
                "A string of attributes separated by spaces."
                "- Default: 'id class style']"
            ],
            'strip_js_on_attributes': [
                True,
                "Strip JavaScript script attribues with the pattern on*. "
                " - Default: True"
            ]
        }
        super(StripHtmlExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        """Strip unwanted HTML attributes and/or comments."""

        md.registerExtension(self)
        config = self.getConfigs()
        striphtml = StripHtmlPostprocessor(
            config.get('strip_comments'),
            config.get('strip_js_on_attributes'),
            config.get('strip_attributes'),
            md
        )
        md.postprocessors.register(striphtml, "strip-html", 1)


def makeExtension(*args, **kwargs):
    """Return extension."""

    return StripHtmlExtension(*args, **kwargs)
