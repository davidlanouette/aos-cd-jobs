from __future__ import absolute_import, print_function, unicode_literals

from actions.named_shell_task import render_task
from .interface import Action

_OCT_INSTALL_TITLE = "INSTALL THE ORIGIN-CI-TOOL"
_OCT_INSTALL_ACTION = """latest="$( readlink "${HOME}/origin-ci-tool/latest" )"
touch "${latest}"
cp "${latest}/bin/activate" "${WORKSPACE}/activate"
cat >> "${WORKSPACE}/activate" <<EOF
export OCT_CONFIG_HOME="${WORKSPACE}/.config"
EOF

source "${WORKSPACE}/activate"
mkdir -p "${OCT_CONFIG_HOME}"
rm -rf "${OCT_CONFIG_HOME}/origin-ci-tool"
if [[ -f /var/lib/jenkins/mirror-os-cred.sh ]]; then
  source /var/lib/jenkins/mirror-os-cred.sh
else
  echo "ERROR: missing file: mirror-os-cred.sh"
  exit 1
fi
oct configure ansible-client verbosity 2
oct configure aws-client 'keypair_name' 'openshift-dev'
oct configure aws-client 'private_key_path' '/var/lib/jenkins/.ssh/openshift-dev.pem'"""


class OCTInstallAction(Action):
    """
    The OCTInstallAction generates a build step
    that installs the `oct` tool in the job work-
    space. Subsequent actions that want to use
    the tool should `source activate` the venv.
    """

    def generate_build_steps(self):
        return [render_task(
            title=_OCT_INSTALL_TITLE,
            command=_OCT_INSTALL_ACTION,
            output_format=self.output_format
        )]
