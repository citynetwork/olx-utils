from __future__ import unicode_literals

import shlex

import sys

from olxutils import cli

# This is extraordinarily ugly, but it's evidently the only option to
# replace sys.stderr with a StringIO instance in a way that it works
# in Python 2 (where sys.stderr is bytes-only) and Python 3 (where
# sys.stderr is unicode-only).
try:
    # Python 2
    from cStringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

from subprocess import Popen, PIPE

from unittest import TestCase


class OLXUtilsCLITestCase(TestCase):
    """
    Run the CLI by importing the cli module and invoking its main() method.
    """

    CLI_PATH = cli.__file__

    def execute_and_check_error(self,
                                cmdline,
                                expected_output):
        try:
            args = shlex.split(cmdline)
            stderr = StringIO()

            sys.argv = args
            sys.stderr = stderr
            with self.assertRaises(SystemExit) as se:
                cli.main(sys.argv)
            self.assertNotEqual(se.exception.code, 0)
            stderr.seek(0)
            self.assertIn(expected_output,
                          stderr.read())
        finally:
            sys.stderr = sys.__stderr__

    def test_invalid_name(self):
        cmdline = '%s _base 2019-01-01 2019-01-31' % self.CLI_PATH
        expected_output = "This run name is reserved."
        self.execute_and_check_error(cmdline,
                                     expected_output)

    def test_end_before_start_date(self):
        cmdline = '%s foo 2019-02-01 2019-01-31' % self.CLI_PATH
        expected_output = "must be greater than or equal"
        self.execute_and_check_error(cmdline,
                                     expected_output)

    def test_invalid_date(self):
        cmdline = '%s foo 2019-02-01 2019-02-31' % self.CLI_PATH
        expected_output = "Not a valid date:"
        self.execute_and_check_error(cmdline,
                                     expected_output)


class OLXUtilsCustomArgsTestCase(OLXUtilsCLITestCase):
    """
    Run the CLI by importing the cli module and invoking its main()
    method, overriding its "args" argument.
    """

    def execute_and_check_error(self,
                                cmdline,
                                expected_output):
        try:
            args = shlex.split(cmdline)
            stderr = StringIO()

            sys.stderr = stderr
            with self.assertRaises(SystemExit) as se:
                cli.main(args)
            self.assertNotEqual(se.exception.code, 0)
            stderr.seek(0)
            self.assertIn(expected_output,
                          stderr.read())
        finally:
            sys.stderr = sys.__stderr__


class OLXUtilsShellTestCase(OLXUtilsCLITestCase):
    """
    Runs the CLI by invoking "olx-new-run" in a subprocess, which
    should be picked up in $PATH.
    """

    # Unqualified name path of the console_script installed by
    # the setup.py entry_points list. This should be dropped in
    # the system PATH, so when we subsequently invoke
    # subprocess.Popen, this should get correctly picked up.
    CLI_PATH = 'olx-new-run'

    # The tests in this class don't use check_call as its use in
    # combination with subprocess.PIPE is strongly discouraged.
    #
    # Reference:
    # https://docs.python.org/3/library/subprocess.html#subprocess.check_call
    def execute_and_check_error(self,
                                cmdline,
                                expected_output):
        args = shlex.split(cmdline)
        p = Popen(args,
                  stderr=PIPE)
        ret = p.wait()
        self.assertNotEqual(ret, 0)
        stdout, stderr = p.communicate()
        self.assertIn(expected_output.encode(),
                      stderr)


class MainModuleTestCase(OLXUtilsShellTestCase):
    """
    Test the __main__.py module, that is, invoking Python with the -m
    package option
    """
    CLI_PATH = '%s -m olxutils' % sys.executable


class NewRunPyTestCase(OLXUtilsShellTestCase):
    """
    # Run the CLI tests with the deprecated compatibility alias
    """
    CLI_PATH = 'new_run.py'
