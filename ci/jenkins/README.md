# The Jenkins controller

A local Jenkins that runs this project's gates and then deploys it onto the machine
it is running on. `../Jenkinsfile` is the pipeline; everything in this directory is
the controller that runs it.

```bash
./ci/jenkins/run.sh            # start it (first run builds the image)
./ci/jenkins/run.sh --reset    # throw JENKINS_HOME away and come back clean
```

Then open http://localhost:8090 as `admin`, password from `pass show elenchus/jenkins-admin`,
and press Build Now on the `elenchus` job.

## The one idea worth having first

Jenkins does not build anything. It is a scheduler with a shell.

Everything this pipeline does, it does by asking a container engine to do it, over a
socket mounted into the controller. So there are two filesystems in play at all times:
the one Jenkins can see, and the one the engine resolves paths against. Almost every
confusing failure in a setup like this is those two disagreeing, and almost every odd
looking decision below exists to keep them in agreement.

## What is actually underneath

This machine has no Docker engine. `/usr/bin/docker` is `podman-docker`, a shim that
forwards to rootless Podman, and `/var/run/docker.sock` is a symlink to the *root*
Podman socket, which is not running. The live one is the user socket at
`$XDG_RUNTIME_DIR/podman/podman.sock`.

That is fine, because Podman serves the Docker API. The controller image installs the
ordinary Docker CLI and `DOCKER_HOST` points it at the Podman socket, so every
`docker` line in the Jenkinsfile is a normal Docker command that happens to be
answered by Podman. Nothing in the pipeline knows or cares.

Three consequences, all of them in `run.sh` with comments:

| Flag | Without it |
| --- | --- |
| `JENKINS_HOME` mounted at the same absolute path inside and out | The engine looks for the build context on the host at a path only the controller has, and reports a missing directory for one Jenkins can read fine |
| `--userns=keep-id` | Rootless id remapping makes container uid 1000 a distant subuid, so the workspace and the socket look root-owned and the `jenkins` user cannot touch them |
| `--security-opt label=disable` | SELinux refuses the confined container a connection to the socket |

And two that bite inside the pipeline rather than at startup:

- **`:z` on every bind mount into a nested container.** The gate containers are
  confined even though the controller is not, so the workspace needs the shared
  SELinux label or they get permission denied on files they can see.
- **Fully qualified image names in the Dockerfiles.** This host sets
  `short-name-mode = "enforcing"`, which refuses an ambiguous name outright when there
  is no TTY to prompt on. Short names inside the compose files are fine, because those
  are resolved by the engine through the Docker API, which defaults to Docker Hub.

## What the pipeline does

| Stage | What happens |
| --- | --- |
| Toolbox images | Builds the two gate images from this directory. Cached after the first run |
| Gates (parallel) | The backend and frontend halves of `.github/workflows/ci.yml`, run at the same time. They share a workspace but not a directory |
| Build images | `docker compose build` against the production compose file |
| Deploy | `docker compose up -d` with `docker-compose.local-deploy.yml` layered on |
| Smoke test | Readiness of the backend and the frontend, checked from inside their own network namespaces |

The backend gate joins the test database's network namespace with
`--network container:`. That looks exotic and is the simplest correct answer:
`backend/tests/conftest.py` hardcodes `localhost:5432` and `scripts/test.sh` probes
that address before running anything, so the database has to *be* localhost. Sharing
the namespace does that without publishing a host port, which means a build cannot
collide with the development stack or with another build.

The gates call `make gate`, not a copy of its steps, for the reason `ci.yml` already
gives in its own `guards` step: a second copy of the list is a list that drifts.

## The controller is disposable

Nothing about this Jenkins is configured by clicking. The image carries the plugins
and `casc.yaml`; `run.sh` writes the job as XML into `JENKINS_HOME/jobs` before Jenkins
boots, which needs no API token and no ordering dance; secrets come from `pass`. So
`--reset` is a normal move, and anything you change in the web UI is gone after one.

If you want the pipeline to do something different, edit `../Jenkinsfile` and commit.
The job builds a branch of this repository from your working copy, so a change has to
be committed to be built, but it does not have to be pushed.

## When it goes wrong

- **`Checkout of Git remote ... aborted because it references a local directory`.**
  `run.sh` should be passing `-Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true`.
  The plugin refuses local paths by default because on a shared controller a job could
  use one to read anything the controller can.
- **`permission denied` on a workspace file inside a gate.** A bind mount is missing
  its `:z`.
- **`short-name resolution enforced but cannot prompt without a TTY`.** An image name
  in one of the Dockerfiles here needs its registry spelled out.
- **The deploy fails but nothing is running to look at.** It is deliberate that a
  failed smoke test leaves the stack up: the container that will not start is the
  evidence. `docker compose -f docker-compose.prod.yml -f ci/jenkins/docker-compose.local-deploy.yml logs`.

## What this is not

This controller holds a socket to your own container engine, so it can do anything
your account can. That is inherent to giving any CI system the ability to build, not
a shortcut taken here, and it is why this is a local-machine tool. A real deployment
runs builds on agents that are not the controller, and does not hand out the engine.
