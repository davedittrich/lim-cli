# LiminalAI CLI utility.
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: https://davedittrich.github.io

"""LiminalAI command line app"""

from __future__ import print_function

# Standard library modules.
import logging
import os
import sys

from lim import __version__
from lim import __release__
from lim.utils import Timer

# External dependencies.

from cliff.app import App
from cliff.commandmanager import CommandManager

if sys.version_info < (3, 6, 0):
    print("The {} program ".format(os.path.basename(sys.argv[0])) +
          "prequires Python 3.6.0 or newer\n" +
          "Found Python {}".format(sys.version), file=sys.stderr)
    sys.exit(1)

BUFFER_SIZE = 128 * 1024
DAY = os.environ.get('DAY', 5)
DEFAULT_PROTOCOLS = ['icmp', 'tcp', 'udp']
KEEPALIVE = 5.0
LIM_DATA_DIR = os.environ.get('LIM_DATA_DIR', os.getcwd())
MAX_LINES = None
MAX_ITEMS = 10
# Use syslog for logging?
# TODO(dittrich): Make this configurable, since it can fail on Mac OS X
SYSLOG = False

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def default_environment(default=None):
    """Return environment identifier"""
    return os.getenv('LIM_ENVIRONMENT', default)


class LiminalApp(App):
    """LiminalAI CLI application"""

    def __init__(self):
        super(LiminalApp, self).__init__(
            description=__doc__.strip(),
            version=__release__ if __release__ != __version__ else __version__,
            command_manager=CommandManager(
                namespace='lim'
            ),
            deferred_help=True,
            )
        self.environment = None
        self.timer = Timer()

    def build_option_parser(self, description, version):
        parser = super(LiminalApp, self).build_option_parser(
            description,
            version
        )

        # Global options
        parser.add_argument(
            '-D', '--data-dir',
            metavar='<data-directory>',
            dest='data_dir',
            default=LIM_DATA_DIR,
            help=('Root directory for holding data files '
                  f'(Env: LIM_DATA_DIR; default: { LIM_DATA_DIR })')
        )
        parser.add_argument(
            '-e', '--elapsed',
            action='store_true',
            dest='elapsed',
            default=False,
            help="Include elapsed time (and ASCII bell) " +
                 "on exit (default: False)"
        )
        parser.add_argument(
            '-E', '--environment',
            metavar='<environment>',
            dest='environment',
            default=default_environment(),
            help="Deployment environment selector " +
            "(Env: LIM_ENVIRONMENT; default: {})".format(
                default_environment())
        )
        parser.add_argument(
            '-n', '--limit',
            action='store',
            type=int,
            metavar='<results_limit>',
            dest='limit',
            default=0,
            help="Limit result to no more than this many items " +
                 "(0 means no limit; default: 0)"
        )
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        self.set_environment(self.options.environment)

    def prepare_to_run_command(self, cmd):
        if cmd.app_args.verbose_level > 1:
            self.LOG.info('[+] command line: {}'.format(
                " ".join([arg for arg in sys.argv])
            ))
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)
        if self.options.elapsed:
            self.timer.start()

    def clean_up(self, cmd, result, err):
        self.LOG.debug('[!] clean_up %s', cmd.__class__.__name__)
        if self.options.elapsed:
            self.timer.stop()
            elapsed = self.timer.elapsed()
            if result != 0:
                self.LOG.debug('[!] elapsed time: %s', elapsed)
            elif self.options.verbose_level > 0 \
                    and cmd.__class__.__name__ != "CompleteCommand":
                self.stdout.write('[+] Elapsed time {}\n'.format(elapsed))
                if sys.stdout.isatty():
                    sys.stdout.write('\a')
                    sys.stdout.flush()

    def set_environment(self, environment=default_environment()):
        """Set variable for current environment"""
        self.environment = environment

    def get_environment(self):
        """Get the current environment setting"""
        return self.environment


def main(argv=sys.argv[1:]):
    """
    Command line interface for the ``lim`` program.
    """

    try:
        myapp = LiminalApp()
        result = myapp.run(argv)
    except KeyboardInterrupt:
        sys.stderr.write("\nReceived keyboard interrupt: exiting\n")
        result = 1
    return result


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# EOF
