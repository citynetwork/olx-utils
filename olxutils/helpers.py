# -*- coding: utf-8 -*-
""" Custom Mako helpers """

import textwrap
import markdown2

from os import environ
from swiftclient.utils import generate_temp_url


class OLXHelpers(object):
    """
    OLX helper methods.

    """
    @staticmethod
    def suffix(s):
        return ' ({})'.format(s) if s else ''

    @staticmethod
    def date(d):
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def markdown(content):
        # Fix up whitespace.
        if content[0] == "\n":
            content = content[1:]
        content.rstrip()
        content = textwrap.dedent(content)

        return markdown2.markdown(content, extras=[
            "code-friendly",
            "fenced-code-blocks",
            "footnotes",
            "tables",
            "use-file-vars",
        ])

    @classmethod
    def markdown_file(cls, filename):
        content = ''
        with open(filename, 'r') as f:
            content = f.read()
        return cls.markdown(content)

    @staticmethod
    def swift_tempurl(path, date):
        swift_endpoint=environ.get('SWIFT_ENDPOINT')
        swift_path=environ.get('SWIFT_PATH')
        swift_tempurl_key=environ.get('SWIFT_TEMPURL_KEY')

        assert(swift_endpoint)
        assert(swift_path)
        assert(swift_tempurl_key)

        path = "{}{}".format(swift_path, path)
        timestamp = int(date.strftime("%s"))
        temp_url = generate_temp_url(path, timestamp, swift_tempurl_key, 'GET', absolute=True)

        return "{}{}".format(swift_endpoint, temp_url)
