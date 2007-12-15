"""
Perform gitosis actions for a git hook.
"""

import errno
import logging
import os
import sys
import shutil

from gitosis import repository
from gitosis import ssh
from gitosis import gitweb
from gitosis import gitdaemon
from gitosis import app
from gitosis import util

def post_update(cfg, git_dir):
    """
    post-update hook for the Gitosis admin directory.

    1. Make an export of the admin repo to a clean directory.
    2. Move the gitosis.conf file to it's destination.
    3. Update the repository descriptions.
    4. Update the projects.list file.
    5. Update the repository export markers.
    6. Update the Gitosis SSH keys.
    """
    export = os.path.join(git_dir, 'gitosis-export')
    try:
        shutil.rmtree(export)
    except OSError, ex:
        if ex.errno == errno.ENOENT:
            pass
        else:
            raise
    repository.export(git_dir=git_dir, path=export)
    os.rename(
        os.path.join(export, 'gitosis.conf'),
        os.path.join(export, '..', 'gitosis.conf'),
        )
    gitweb.set_descriptions(
        config=cfg,
        )
    generated = util.getGeneratedFilesDir(config=cfg)
    gitweb.generate_project_list(
        config=cfg,
        path=os.path.join(generated, 'projects.list'),
        )
    gitdaemon.set_export_ok(
        config=cfg,
        )
    ssh.writeAuthorizedKeys(
        path=os.path.expanduser('~/.ssh/authorized_keys'),
        keydir=os.path.join(export, 'keydir'),
        )

class Main(app.App):
    """gitosis-run-hook program."""
    # W0613 - They also might ignore arguments here, where the descendant
    # methods won't.
    # pylint: disable-msg=W0613

    def create_parser(self):
        """Declare the input for this program."""
        parser = super(Main, self).create_parser()
        parser.set_usage('%prog [OPTS] HOOK')
        parser.set_description(
            'Perform gitosis actions for a git hook')
        return parser

    def handle_args(self, parser, cfg, options, args):
        """Parse the input for this program."""
        try:
            (hook,) = args
        except ValueError:
            parser.error('Missing argument HOOK.')

        log = logging.getLogger('gitosis.run_hook')
        os.umask(0022)

        git_dir = os.environ.get('GIT_DIR')
        if git_dir is None:
            log.error('Must have GIT_DIR set in enviroment')
            sys.exit(1)

        if hook == 'post-update':
            log.info('Running hook %s', hook)
            post_update(cfg, git_dir)
            log.info('Done.')
        else:
            log.warning('Ignoring unknown hook: %r', hook)
