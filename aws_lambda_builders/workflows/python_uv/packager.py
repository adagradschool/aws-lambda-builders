"""
Installs packages using UV
"""

import logging
from aws_lambda_builders.architecture import ARM64, X86_64
from .utils import OSUtils
from aws_lambda_builders.actions import ActionFailedError

LOG = logging.getLogger(__name__)

class SubprocessUv:
    """
    Wrapper around uv
    """

    def __init__(self, osutils=None, uv_path=None, env=None):
        if osutils is None:
            osutils = OSUtils()
        self._osutils = osutils
        self.uv_path = uv_path
        self.env = env

    def run(self, args: list[str], env_vars=None) -> str:
        if env_vars is None:
            env_vars = {}
        p = self._osutils.popen([self.uv_path] + args, stdout=self._osutils.pipe, stderr=self._osutils.pipe, env={**self.env, **env_vars})
        out, err = p.communicate()
        rc = p.returncode
        if rc != 0:
            LOG.error(err.decode())
            raise ActionFailedError("Failed to run command: uv ", " ".join(args))
        return out.decode()