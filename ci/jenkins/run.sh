#!/usr/bin/env bash
# Start (or restart) the Jenkins controller for this project on the local machine.
#
#   ./ci/jenkins/run.sh          start it, building the image if needed
#   ./ci/jenkins/run.sh --reset  destroy JENKINS_HOME first and come back clean
#
# The controller is disposable: everything that defines it lives in this directory
# (Dockerfile, plugins.txt, casc.yaml) and in the job config this script seeds, so
# --reset is a supported move rather than a last resort.
#
# Every flag below is load-bearing on a rootless-Podman Fedora host. The comments say
# why, because each one fails differently and unhelpfully if dropped.
set -euo pipefail

cd "$(dirname "$0")/../.."
REPO_DIR="$(pwd)"

IMAGE=localhost/elenchus-jenkins:lts
NAME=elenchus-jenkins
JOB=elenchus

# Not 8080. Jenkins' default collides with the Node processes already holding 8080 and
# 8081 on this machine, and the collision shows up as a container that starts and then
# dies rather than as a clear "address in use".
HTTP_PORT=8090

# Which branch the seeded job builds. The Jenkinsfile is read from the branch, so
# changing the pipeline means committing to this branch, not editing a text box.
BRANCH="${ELENCHUS_BRANCH:-feat/jenkins-pipeline}"

# JENKINS_HOME is bind-mounted at THE SAME ABSOLUTE PATH inside and outside the
# container, rather than at the image's own /var/jenkins_home. This is the trick that
# makes a socket-mounted controller work at all:
#
# Jenkins builds nothing itself. It asks the engine on the other end of the socket,
# and that engine resolves every path against the HOST filesystem. So when the
# pipeline says `-v "$WORKSPACE:$WORKSPACE"`, that path has to mean the same directory
# on both sides. Mount the workspace anywhere else and the engine reports an empty or
# missing directory for one Jenkins can read perfectly well.
JENKINS_HOME_DIR="$HOME/jenkins_home"

# The live engine socket. NOT /var/run/docker.sock, which on this host is a symlink to
# the ROOT Podman socket and is not running. This is the user socket systemd keeps up.
PODMAN_SOCK="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"

if [ ! -S "$PODMAN_SOCK" ]; then
    echo "No Podman socket at $PODMAN_SOCK" >&2
    echo "Start it with:  systemctl --user enable --now podman.socket" >&2
    exit 1
fi

# Secrets come from the password store, never from a file next to this script and
# never from a default baked into casc.yaml. Generated on first run, reused after.
secret() {
    local entry="$1"
    pass show "$entry" 2>/dev/null || {
        pass generate -n "$entry" 32 >/dev/null
        pass show "$entry"
    }
}

JENKINS_ADMIN_PASSWORD="$(secret elenchus/jenkins-admin)"
ELENCHUS_POSTGRES_PASSWORD="$(secret elenchus/postgres)"

if [ "${1:-}" = "--reset" ]; then
    echo "--> destroying $JENKINS_HOME_DIR"
    podman rm -f "$NAME" 2>/dev/null || true
    rm -rf "$JENKINS_HOME_DIR"
fi

podman image exists "$IMAGE" || {
    echo "--> building $IMAGE"
    podman build -t elenchus-jenkins:lts -f ci/jenkins/Dockerfile ci/jenkins
}

# The job, seeded as XML on disk before Jenkins boots rather than created through the
# UI or the REST API afterwards. Jenkins reads jobs/ at startup, so this needs no
# credentials, no API token and no ordering dance, and it keeps the job definition in
# version control with everything else. Build history lives in jobs/*/builds and is
# untouched by rewriting config.xml.
#
# The SCM URL is a local path, not the GitHub remote: the repository is mounted into
# the container below, so Jenkins clones from your working copy. That means a branch
# only has to be committed to be built, not pushed.
mkdir -p "$JENKINS_HOME_DIR/jobs/$JOB"
cat > "$JENKINS_HOME_DIR/jobs/$JOB/config.xml" <<XML
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>Elenchus: the CI gates, then a local deployment of docker-compose.prod.yml.</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>${REPO_DIR}</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/${BRANCH}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>false</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

podman rm -f "$NAME" 2>/dev/null || true

echo "--> starting $NAME on http://localhost:$HTTP_PORT"
podman run -d \
    --name "$NAME" \
    --restart unless-stopped \
    -p "${HTTP_PORT}:8080" \
    \
    `# Rootless Podman remaps ids: without keep-id, container uid 0 is host uid 1000` \
    `# and container uid 1000 is a subuid far away. The socket, JENKINS_HOME and the` \
    `# repository are all owned by host 1000, so to the jenkins user (uid 1000 in the` \
    `# image) they would look root-owned and be unusable. keep-id maps 1000 to 1000.` \
    --userns=keep-id \
    \
    `# SELinux is enforcing on Fedora and a confined container cannot connect to the` \
    `# socket. The usual ":z" relabel is the wrong tool for this particular file: it` \
    `# would rewrite the label on the HOST's live Podman socket, which the host's own` \
    `# podman then has to keep working with. Disabling confinement for this one` \
    `# container is the narrower change.` \
    `#` \
    `# Be clear about what it buys and costs. A container holding this socket can` \
    `# drive the engine as your user, so it can do anything your account can. That is` \
    `# inherent to giving any CI system a build socket, not to this flag, and it is` \
    `# why this controller is a local-machine tool and not a template for a server.` \
    --security-opt label=disable \
    \
    -v "$JENKINS_HOME_DIR:$JENKINS_HOME_DIR" \
    -v "$PODMAN_SOCK:$PODMAN_SOCK" \
    `# The working copy, read-only, at its own path. Jenkins clones from it.` \
    -v "$REPO_DIR:$REPO_DIR:ro" \
    -e "JENKINS_HOME=$JENKINS_HOME_DIR" \
    \
    `# What makes the stock Docker CLI talk to Podman. Podman serves the Docker API on` \
    `# this socket, so the client neither knows nor cares which engine answers.` \
    -e "DOCKER_HOST=unix://$PODMAN_SOCK" \
    \
    `# Read by casc.yaml. Present in the container environment, so anyone who can run` \
    `# podman inspect on this box can read them; that is the same person who can read` \
    `# the password store, so it is not a new exposure here. It would be on a server.` \
    -e "JENKINS_ADMIN_PASSWORD=$JENKINS_ADMIN_PASSWORD" \
    -e "ELENCHUS_POSTGRES_PASSWORD=$ELENCHUS_POSTGRES_PASSWORD" \
    \
    `# The wizard is off because casc.yaml already does everything it would ask for.` \
    `#` \
    `# ALLOW_LOCAL_CHECKOUT lifts the Git plugin's refusal to clone from a local` \
    `# directory. The refusal is not paranoia: on a shared controller, a job whose SCM` \
    `# URL is a path can read any directory the controller can, so the plugin makes` \
    `# that a deliberate choice rather than a default. Here the controller is yours,` \
    `# and the only path it can reach is this repository, mounted read-only above.` \
    -e "JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true" \
    \
    "$IMAGE"

echo "--> waiting for Jenkins to answer"
for _ in $(seq 1 90); do
    if curl -fsS -o /dev/null "http://localhost:$HTTP_PORT/login" 2>/dev/null; then
        echo
        echo "  Jenkins   http://localhost:$HTTP_PORT"
        echo "  User      admin"
        echo "  Password  pass show elenchus/jenkins-admin"
        echo "  Job       $JOB  (building $BRANCH from $REPO_DIR)"
        exit 0
    fi
    sleep 2
done

echo "Timed out. Logs:" >&2
podman logs --tail 60 "$NAME" >&2
exit 1
