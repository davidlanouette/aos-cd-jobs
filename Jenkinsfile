#!/usr/bin/env groovy
node {
    checkout scm
    load("pipeline-scripts/commonlib.groovy").describeJob("kam_sync", """
        -----------------------------------
        Sync OpenShift kam client to mirror
        -----------------------------------
        http://mirror.openshift.com/pub/openshift-v4/x86_64/clients/kam/

        Timing: This is only ever run by humans, upon request.
    """)
}

pipeline {
    agent any
    options { disableResume() }

    parameters {
        string(
            name: "VERSION",
            description: "Desired version name. Example: v1.0.0",
            defaultValue: "",
            trim: true,
        )
        string(
            name: "SOURCES_LOCATION",
            description: "Example: http://download.eng.bos.redhat.com/staging-cds/developer/openshift-gitops-kam/1.0.0-78/signed/all/",
            defaultValue: "",
            trim: true,
        )
    }

    stages {
        stage("Validate params") {
            steps {
                script {
                    if (!params.VERSION) {
                        error "VERSION must be specified"
                    }
                }
            }
        }
        stage("Clean working dir") {
            steps {
                sh "rm -rf ${params.VERSION}"
            }
        }
        stage("Download binaries") {
            steps {
                script {
                    downloadRecursive(params.SOURCES_LOCATION, params.VERSION)
                }
            }
        }
        stage("Sync to mirror") {
            steps {
                sh "tree ${params.VERSION}"
                commonlib.syncDirToS3Mirror("${params.VERSION}/", "/pub/openshift-v4/x86_64/clients/kam/${params.VERSION}/")
                commonlib.syncDirToS3Mirror("${params.VERSION}/", "/pub/openshift-v4/x86_64/clients/kam/latest/")
            }
        }
    }
}

def downloadRecursive(path, destination) {
    sh "wget --recursive --no-parent --reject 'index.html*' --no-directories --directory-prefix ${destination} ${path}"
}
