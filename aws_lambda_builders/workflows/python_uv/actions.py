"""
Action to resolve Python dependencies using UV
"""
import shlex
import typing as t
import logging
from aws_lambda_builders.actions import ActionFailedError, BaseAction, Purpose
from aws_lambda_builders.architecture import X86_64
from aws_lambda_builders.workflows.python_uv.packager import SubprocessUv
from aws_lambda_builders.utils import which
from aws_lambda_builders.workflows.python_pip.utils import OSUtils
import tempfile

LOG = logging.getLogger(__name__)


class PythonUvBuildAction(BaseAction):
    NAME = "ResolveDependencies"
    DESCRIPTION = "Installing dependencies from UV"
    PURPOSE = Purpose.RESOLVE_DEPENDENCIES
    LANGUAGE = "python"

    def _setup_venv(self) -> dict[str, t.Any]:
        env = self._os_utils.original_environ().copy()
        self.venv_path = f"{self.scratch_dir}/venv"
        env["UV_PROJECT_ENVIRONMENT"] = self.venv_path
        self.env = env

    def __init__(
        self, artifacts_dir, scratch_dir, manifest_path, runtime, dependencies_dir, binaries, architecture=X86_64
    ):
        self.artifacts_dir = artifacts_dir
        self.manifest_path = manifest_path
        self.scratch_dir = scratch_dir
        self.runtime = runtime
        self.dependencies_dir = dependencies_dir
        self.binaries = binaries
        self.architecture = architecture
        self._os_utils = OSUtils()
        self._setup_venv()
        # TODO : Map from architecture to platform
        self.platform = "x86_64-manylinux_2_17"
        # TODO : map from runtime to python version
        self.py_version = "3.11"

    def execute(self) -> None:
        """
        Executes the build action for Python `uv` workflows.
        """
        uv = self._find_uv()
        uv.run(args=shlex.split("sync --quiet"))
        requirements = uv.run(args=shlex.split("export --no-dev --locked --no-installer-metadata --no-hashes --no-header --quiet"))
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(requirements.encode())
        temp.close()
        uv.run(args=shlex.split(f"pip install --no-installer-metadata --no-compile-bytecode --python-platform {self.platform} --python {self.py_version} --target {self.artifacts_dir} -r {temp.name}"))

        
    def _find_uv(self) -> SubprocessUv:
        uv_binaries = which("uv")
        if not uv_binaries:
            raise ActionFailedError("No uv found in PATH")
        return SubprocessUv(osutils=self._os_utils, uv_path=uv_binaries[0], env=self.env)
