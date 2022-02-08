from __future__ import absolute_import, print_function, unicode_literals

from jinja2 import Template

from .forward_parameter import ForwardParametersAction
from .interface import Action
from .named_shell_task import render_task
from .script import ScriptAction

_PARAMETER_TEMPLATE = Template("""        <hudson.model.StringParameterDefinition>
          <name>{{ name }}</name>
          <description>{{ description }}</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>""")

_GCS_UPLOAD = """docker run -e JOB_SPEC="${JOB_SPEC}" -v /data:/data:z registry.ci.openshift.org/ci/initupload:latest --clone-log=/data/clone.json --dry-run=false --gcs-path=gs://origin-ci-test --gcs-credentials-file=/data/credentials.json --path-strategy=single --default-org=openshift --default-repo=origin
"""

_CLONEREFS_ACTION_TEMPLATE = Template("""JOB_SPEC="$( jq --compact-output '.buildid |= "'"${BUILD_NUMBER}"'"' <<<"${JOB_SPEC}" )"
for image in 'registry.ci.openshift.org/ci/clonerefs:latest' 'registry.ci.openshift.org/ci/initupload:latest'; do
    for (( i = 0; i < 5; i++ )); do
        if docker pull "${image}"; then
            break
        fi
    done
done
clonerefs_args=${CLONEREFS_ARGS:-{% for repo in repos %}--repo={{repo}} {% endfor %}}
docker run -v /data:/data:z registry.ci.openshift.org/ci/clonerefs:latest --src-root=/data --log=/data/clone.json ${PULL_REFS:+--repo=${REPO_OWNER},${REPO_NAME}=${PULL_REFS}} ${clonerefs_args}
{{upload_to_gcs_step}}
sudo chmod -R a+rwX /data
sudo chown -R origin:origin-git /data
""")


class ClonerefsAction(Action):
    """
    A ClonerefsAction generates a build step that
    synchronizes repositories on the remote host
    """

    def __init__(self, repos):
        self.repos = repos

    def generate_parameters(self):
        return [
            _PARAMETER_TEMPLATE.render(name='JOB_SPEC', decsription='JSON form of job specification.'),
            _PARAMETER_TEMPLATE.render(name='buildId', decsription='Unique build number for each run.'),
            _PARAMETER_TEMPLATE.render(name='BUILD_ID', decsription='Unique build number for each run.'),
            _PARAMETER_TEMPLATE.render(name='REPO_OWNER', decsription='GitHub org that triggered the job.'),
            _PARAMETER_TEMPLATE.render(name='REPO_NAME', decsription='GitHub repo that triggered the job.'),
            _PARAMETER_TEMPLATE.render(name='PULL_BASE_REF', decsription='Ref name of the base branch.'),
            _PARAMETER_TEMPLATE.render(name='PULL_BASE_SHA', decsription='Git SHA of the base branch.'),
            _PARAMETER_TEMPLATE.render(name='PULL_REFS', decsription='All refs to test.'),
            _PARAMETER_TEMPLATE.render(name='PULL_NUMBER', decsription='Pull request number.'),
            _PARAMETER_TEMPLATE.render(name='PULL_PULL_SHA', decsription='Pull request head SHA.'),
            _PARAMETER_TEMPLATE.render(name='CLONEREFS_ARGS', decsription='Pull request head SHA.'),
        ]

    def generate_build_steps(self):
        steps = []
        upload_to_gcs_step = ""
        if self.output_format == "xml":
            steps = [render_task(
                    title="FORWARD GCS CREDENTIALS TO REMOTE HOST",
                    command="""for (( i = 0; i < 10; i++ )); do
            if scp -F ${WORKSPACE}/.config/origin-ci-tool/inventory/.ssh_config /var/lib/jenkins/.config/gcloud/gcs-publisher-credentials.json openshiftdevel:/data/credentials.json; then
                break
            fi
    done
    for (( i = 0; i < 10; i++ )); do
            if scp -F ${WORKSPACE}/.config/origin-ci-tool/inventory/.ssh_config /var/lib/jenkins/mirror-os-cred.sh openshiftdevel:/data/mirror-os-cred.sh; then
                break
            fi
    done

    for (( i = 0; i < 10; i++ )); do
            if scp -F ${WORKSPACE}/.config/origin-ci-tool/inventory/.ssh_config /var/lib/jenkins/tweaks/*.rpm openshiftdevel:/data/; then
                break
            fi
    done

    for (( i = 0; i < 10; i++ )); do
            if scp -F ${WORKSPACE}/.config/origin-ci-tool/inventory/.ssh_config /var/lib/jenkins/tweaks/good_repos_rhui.tgz openshiftdevel:/data/; then
                break
            fi
    done""",
                    output_format=self.output_format
                )
            ]
            upload_to_gcs_step = _GCS_UPLOAD



        forward_action = ForwardParametersAction(
            parameters=['JOB_SPEC', 'buildId', 'BUILD_ID', 'REPO_OWNER', 'REPO_NAME', 'PULL_BASE_REF', 'PULL_BASE_SHA',
            'PULL_REFS', 'PULL_NUMBER', 'PULL_PULL_SHA', 'JOB_SPEC', 'BUILD_NUMBER', 'CLONEREFS_ARGS']
        )
        forward_action.output_format = self.output_format
        steps += forward_action.generate_build_steps()

        script_action = ScriptAction(
            repository=None,
            title="SYNC REPOSITORIES",
            script=_CLONEREFS_ACTION_TEMPLATE.render(repos=self.repos, upload_to_gcs_step=upload_to_gcs_step),
            timeout=None,
            output_format=self.output_format
        )
        steps += script_action.generate_build_steps()

        return steps
