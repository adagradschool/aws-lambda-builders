"""
Python UV Workflow
"""

import logging

from aws_lambda_builders.actions import CopySourceAction
from aws_lambda_builders.path_resolver import PathResolver
from aws_lambda_builders.workflow import BaseWorkflow, BuildDirectory, BuildInSourceSupport, Capability
from aws_lambda_builders.workflows.python_pip.validator import PythonRuntimeValidator
from aws_lambda_builders.workflows.python_uv.constants import EXCLUDED_FILES
from .actions import PythonUvBuildAction
from .utils import OSUtils

LOG = logging.getLogger(__name__)

class PythonUvWorkflow(BaseWorkflow):
    NAME = "PythonUvBuilder"
    CAPABILITY = Capability(language="python", dependency_manager="uv", application_framework=None)
    PYTHON_VERSION_THREE = "3"
    DEFAULT_BUILD_DIR = BuildDirectory.SCRATCH
    BUILD_IN_SOURCE_SUPPORT = BuildInSourceSupport.NOT_SUPPORTED

    def __init__(self, source_dir, artifacts_dir, scratch_dir, manifest_path, runtime=None, osutils=None, **kwargs):
        super(PythonUvWorkflow, self).__init__(
            source_dir, artifacts_dir, scratch_dir, manifest_path, runtime=runtime, **kwargs
        )
        if osutils is None:
            osutils = OSUtils()

        if not self.download_dependencies and not self.dependencies_dir:
            LOG.info(
                "download_dependencies is False and dependencies_dir is None. Copying the source files into the "
                "artifacts directory. "
            )

        self.actions = []
        if not osutils.file_exists(manifest_path):
            LOG.warning("pyproject.toml file not found. Continuing the build without dependencies.")
            self.actions.append(CopySourceAction(source_dir, artifacts_dir, excludes=EXCLUDED_FILES))
            return

        # If a pyproject.toml exists, run uv builder before copy action.
        self.actions.append(
            PythonUvBuildAction(
                artifacts_dir,
                scratch_dir,
                manifest_path,
                runtime,
                self.dependencies_dir,
                binaries=self.binaries,
                architecture=self.architecture,
            )
        )
        self.actions.append(CopySourceAction(source_dir, artifacts_dir, excludes=EXCLUDED_FILES))

    def get_resolvers(self):
        """
        Specialized Python path resolver that looks for additional binaries in addition to the language specific binary.
        """
        return [
            PathResolver(
                runtime=self.runtime,
                binary=self.CAPABILITY.language,
                additional_binaries=self._get_additional_binaries(),
                executable_search_paths=self.executable_search_paths,
            )
        ]

    def _get_additional_binaries(self):
        # python3 is an additional binary that has to be considered in addition to the original python binary, when
        # the specified python runtime is 3.x
        major, _ = self.runtime.replace(self.CAPABILITY.language, "").split(".")
        return [f"{self.CAPABILITY.language}{major}"] if major == self.PYTHON_VERSION_THREE else None

    def get_validators(self):
        return [PythonRuntimeValidator(runtime=self.runtime, architecture=self.architecture)]
