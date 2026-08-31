# The Jenkins controller this project's pipeline runs on.
#
# Stock jenkins/jenkins:lts has no container tooling at all, and the pipeline is
# almost entirely container work: it builds the two images, brings the prod stack
# up and tears it down again. So the CLI has to be in here.
#
# There is no Docker engine on the target machine. `docker` there is podman-docker
# forwarding to rootless Podman, which serves the Docker API on a unix socket. That
# is why the Docker CLI is the right client despite Podman being the engine: it
# speaks the API Podman implements, and DOCKER_HOST (set at run time, see run.sh)
# points it at the mounted socket. Nothing in here needs to know it is Podman.
# Fully qualified: this host sets short-name-mode = "enforcing" in registries.conf,
# which refuses an ambiguous name outright when there is no TTY to prompt on. A
# bare `jenkins/jenkins:lts` builds fine by hand and fails in any automated build.
FROM docker.io/jenkins/jenkins:lts

USER root

# make and git: `make gate` and `make front-gate` are what CI runs, and the pipeline
# delegates to them rather than restating the check list, for the same reason
# .github/workflows/ci.yml delegates its guards step to the Makefile. A second copy
# of the list is a list that drifts.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make git curl ca-certificates gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
        -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        docker-ce-cli docker-compose-plugin \
    && apt-get purge -y gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Plugins baked in, so the controller image is the whole controller. Installing them
# through the setup wizard instead would make a fresh JENKINS_HOME depend on a network
# round trip to the update centre and on whoever clicks it choosing the same set.
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Jenkins' own configuration, applied at boot by the configuration-as-code plugin.
# Kept under /usr/share/jenkins/ref rather than in JENKINS_HOME because JENKINS_HOME
# is the bind-mounted, disposable half; this is part of the image.
COPY casc.yaml /usr/share/jenkins/ref/casc/jenkins.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc/jenkins.yaml

USER jenkins
