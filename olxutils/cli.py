#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
New course run
"""
from __future__ import unicode_literals

import sys

import os

from argparse import ArgumentParser, ArgumentTypeError

from datetime import datetime
from subprocess import check_call, CalledProcessError
from mako import exceptions

from olxutils.templates import OLXTemplates

# Under which name do we expect the CLI to be generally called?
CANONICAL_COMMAND_NAME = 'olx'


class CLI(object):

    def parse_args(self, args=sys.argv[1:]):

        def valid_date(s):
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except ValueError:
                msg = "Not a valid date: '{0}'.".format(s)
                raise ArgumentTypeError(msg)

        parser = ArgumentParser(prog=CANONICAL_COMMAND_NAME,
                                description="Open Learning XML (OLX) utility")

        subparsers = parser.add_subparsers(dest='subcommand')
        new_run_help = 'Prepare a local source tree for a new course run'
        new_run_parser = subparsers.add_parser('new-run',
                                               help=new_run_help)

        new_run_parser.add_argument('-b', "--create-branch",
                                    action="store_true",
                                    help=("Create a new 'run/NAME' "
                                          "git branch, add changed files, "
                                          "and commit them."))
        new_run_parser.add_argument('-p', "--public",
                                    action="store_true",
                                    help="Make the course run public")
        new_run_parser.add_argument('-s', "--suffix",
                                    help="The run name suffix")
        new_run_parser.add_argument("name",
                                    help="The run identifier")
        new_run_parser.add_argument("start_date",
                                    type=valid_date,
                                    help="When the course run starts "
                                         "(YYYY-MM-DD)")
        new_run_parser.add_argument("end_date",
                                    type=valid_date,
                                    help="When the course run ends "
                                         "(YYYY-MM-DD)")

        self.opts = parser.parse_args(args)

        if self.opts.name == "_base":
            message = "This run name is reserved.  Please choose another one."
            new_run_parser.error(message)

        if self.opts.end_date < self.opts.start_date:
            message = ("End date [{:%Y-%m-%d}] "
                       "must be greater than or equal "
                       "to start date [{:%Y-%m-%d}].")
            new_run_parser.error(message.format(self.opts.end_date,
                                                self.opts.start_date))

    def check_branch(self):
        try:
            check_call("git rev-parse --verify run/{}".format(self.opts.name),
                       shell=True)
        except CalledProcessError:
            pass
        else:
            message = (
                "The target git branch already exists.  "
                "Please delete it and try again.\n"
                "You can do so with: \n"
                "\n"
                "git branch -d run/{}\n"
            )
            sys.stderr.write(message.format(self.opts.name))
            sys.exit(1)

        try:
            check_call("git checkout -b run/{}".format(self.opts.name),
                       shell=True)
        except CalledProcessError:
            message = "Error creating branch 'run/{}'\n"
            sys.stderr.write(message.format(self.opts.name))
            sys.exit(1)

    def render_templates(self):
        # Render templates
        templates = OLXTemplates({
            "run_name": self.opts.name,
            "start_date": self.opts.start_date,
            "end_date": self.opts.end_date.replace(hour=23,
                                                   minute=59,
                                                   second=59),
            "run_suffix": self.opts.suffix,
            "is_public": self.opts.public,
        })

        try:
            templates.render()
        except:  # noqa: E722
            message = exceptions.text_error_template().render()
            sys.stderr.write(message)
            sys.exit(1)

    def create_symlinks(self):
        # Create symlink for policies
        try:
            check_call("ln -sf _base policies/{}".format(self.opts.name),
                       shell=True)
        except CalledProcessError:
            sys.stderr.write("Error creating policies symlink.\n")
            sys.exit(1)

    def create_branch(self):
        # Git add the changed files and commit them.
        try:
            check_call("git add .",
                       shell=True)
            check_call("git commit -m 'New run: {}'".format(self.opts.name),
                       shell=True)
        except CalledProcessError:
            sys.stderr.write("Error commiting new run.\n")
            sys.exit(1)

    def show_branch_message(self):
        message = (
            "\n"
            "To push this new branch upstream, run:\n"
            "\n"
            "$ git push -u origin run/{}\n"
            "\n"
            "To switch back to master, run:\n"
            "\n"
            "$ git checkout master\n"
        )
        sys.stderr.write(message.format(self.opts.name))

    def new_run(self):
        if self.opts.create_branch:
            self.check_branch()

        self.render_templates()

        self.create_symlinks()

        if self.opts.create_branch:
            self.create_branch()
            self.show_branch_message()

        sys.stderr.write("All done!\n")

    def main(self, argv=sys.argv):
        """Main CLI entry point.

        Checks how we were invoked: either we're being called as just
        "olx" or "__main__", in which case we can pass the subcommands
        right through to the argument parser and its subparser(s).

        Or we were called the old way (as olx-new-run), in which case we
        mangle the system arguments to inject the subcommand.

        Or we were called the *really* old way (as new_run.py), in which
        case we pretend we got "new-run" as the subcommand.
        """
        prefix = '%s-' % CANONICAL_COMMAND_NAME
        command = argv[0]

        if os.path.basename(command) == 'new_run.py':
            # Mangle the command into "olx new-run".
            argv[0] = os.path.join(os.path.dirname(command),
                                   CANONICAL_COMMAND_NAME)
            argv.insert(1, 'new-run')
        elif os.path.basename(command).startswith(prefix):
            # Drop the prefix, i.e. turn "olx-foo" into "olx foo".
            argv[0] = os.path.join(os.path.dirname(command),
                                   CANONICAL_COMMAND_NAME)
            argv.insert(1,
                        os.path.basename(command).replace(prefix, ''))

        self.parse_args(argv[1:])

        # We could use getattr() here, but even with all our
        # safeguards in place subcommand is still user input. So just
        # enumerate and repeat the method names here.
        if self.opts.subcommand == 'new-run':
            self.new_run()


def main(argv=sys.argv):
    CLI().main(argv)


if __name__ == "__main__":
    main()
