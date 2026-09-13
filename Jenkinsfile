// The Jenkins pipeline for Elenchus: the gates from .github/workflows/ci.yml, then a
// deployment of docker-compose.prod.yml onto the machine Jenkins runs on.
//
// How to stand the controller up, and why each of its run flags exists, is in
// ci/jenkins/README.md. The short version of the one fact this file depends on:
// Jenkins builds nothing itself. Every `docker` line below is a request to an engine
// on the other end of a mounted socket, and that engine resolves paths against the
// HOST filesystem. JENKINS_HOME is therefore mounted at the same absolute path inside
// and outside the controller, which is what lets `-v "$WORKSPACE:$WORKSPACE"` mean
// the same directory to both.

pipeline {
    agent any

    options {
        timestamps()
        // The deploy stage owns fixed host ports and a single named compose project.
        // Two builds at once would fight over both and the loser's failure would look
        // like a bug in the app.
        disableConcurrentBuilds()
        timeout(time: 90, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        // Toolbox images, built by the first stage and cached by the engine after that.
        BACKEND_GATE_IMAGE  = 'elenchus-backend-gate:ci'
        FRONTEND_GATE_IMAGE = 'elenchus-frontend-gate:ci'

        // Per-build name, so a container left behind by a killed build never collides
        // with the next one. The `post` block removes it either way.
        PG_CTR = "elenchus-gate-pg-${BUILD_NUMBER}"

        // Dependency caches that survive the build. Without these every run
        // re-downloads the whole dependency tree, which is most of the wall clock.
        UV_CACHE_VOLUME   = 'elenchus-ci-uv-cache'
        PNPM_STORE_VOLUME = 'elenchus-ci-pnpm-store'

        COMPOSE = 'docker compose -f docker-compose.prod.yml -f ci/jenkins/docker-compose.local-deploy.yml'

        // Read from the Jenkins credential store, not from this file. Jenkins masks it
        // in the console output. docker-compose.prod.yml declares it `${POSTGRES_PASSWORD:?}`,
        // so an unset value stops the deploy rather than quietly installing a database
        // with a well-known password.
        POSTGRES_PASSWORD = credentials('elenchus-postgres-password')

        // Where this deployment answers. NEXT_PUBLIC_API_URL is baked into the browser
        // bundle at build time, so it has to be the origin a browser on this machine
        // will actually use, which is why ci/jenkins/docker-compose.local-deploy.yml
        // publishes the backend at all.
        BACKEND_PORT        = '8000'
        FRONTEND_PORT       = '3000'
        FRONTEND_ORIGIN     = 'http://localhost:3000'
        NEXT_PUBLIC_API_URL = 'http://localhost:8000'

        // Off, so this pipeline needs no model key. The gates already run without one
        // by design (the suite fakes the LLM at the client wrapper), and the smoke test
        // checks that the service is up, not that it can draft a survey. Enabling a tier
        // with an empty key would deploy something that boots green and 503s every model
        // call, which is worse than plainly not having the feature on.
        LLM_TIER1_ENABLED = 'false'
    }

    stages {

        stage('Toolbox images') {
            steps {
                sh '''
                    set -eu
                    docker build -t "$BACKEND_GATE_IMAGE"  -f ci/jenkins/backend-gate.Dockerfile  ci/jenkins
                    docker build -t "$FRONTEND_GATE_IMAGE" -f ci/jenkins/frontend-gate.Dockerfile ci/jenkins
                '''
            }
        }

        // The two halves of .github/workflows/ci.yml, which are two independent jobs
        // there and are two parallel branches here. They share a workspace but not a
        // directory: one only touches backend/, the other only frontend/.
        stage('Gates') {
            parallel {

                stage('Backend') {
                    steps {
                        sh '''
                            set -eu

                            # The suite runs against a real Postgres rather than SQLite, so the
                            # repository layer is exercised against the engine it ships on. Same
                            # reasoning, and the same credentials, as ci.yml's `services:` block.
                            docker rm -f "$PG_CTR" >/dev/null 2>&1 || true
                            docker run -d --name "$PG_CTR" \
                                -e POSTGRES_USER=elenchus \
                                -e POSTGRES_PASSWORD=elenchus \
                                -e POSTGRES_DB=elenchus \
                                docker.io/library/postgres:17-alpine >/dev/null

                            echo "--> waiting for postgres"
                            for _ in $(seq 1 40); do
                                docker exec "$PG_CTR" pg_isready -U elenchus -d elenchus >/dev/null 2>&1 && break
                                sleep 2
                            done
                            docker exec "$PG_CTR" pg_isready -U elenchus -d elenchus

                            # --network container: puts the gate in the database's own network
                            # namespace, so "localhost:5432" inside the gate IS the database.
                            # That address is not a preference: backend/tests/conftest.py hardcodes
                            # it, and scripts/test.sh probes it before running anything. Sharing the
                            # namespace satisfies both without publishing a host port, so this build
                            # cannot collide with the development stack or with another build.
                            #
                            # No -u flag. Under rootless Podman the host account owning the
                            # workspace maps to root inside the container, so the default root user
                            # is the one that can read and write these files; forcing uid 1000 would
                            # produce permission errors on a directory Jenkins itself owns.
                            docker run --rm \
                                --network "container:$PG_CTR" \
                                -v "$WORKSPACE:$WORKSPACE:z" \
                                -v "$UV_CACHE_VOLUME:/root/.cache/uv" \
                                -w "$WORKSPACE/backend" \
                                -e DATABASE_URL=postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus \
                                "$BACKEND_GATE_IMAGE" \
                                bash -euc '
                                    uv sync --locked
                                    echo "--> migrations apply from scratch"
                                    uv run alembic upgrade head
                                    echo "--> make gate"
                                    cd .. && make gate
                                '
                        '''
                    }
                    post {
                        always {
                            sh 'docker rm -f "$PG_CTR" >/dev/null 2>&1 || true'
                        }
                    }
                }

                stage('Frontend') {
                    steps {
                        // The check list is ci.yml's, not the Makefile's. `make front-gate`
                        // execs into an already-running development container, which is the
                        // right tool at a desk with the stack up and the wrong one here, where
                        // nothing is running yet and the point is to check the committed source.
                        sh '''
                            set -eu
                            docker run --rm \
                                -v "$WORKSPACE:$WORKSPACE:z" \
                                -v "$PNPM_STORE_VOLUME:/pnpm-store" \
                                -w "$WORKSPACE/frontend" \
                                "$FRONTEND_GATE_IMAGE" \
                                bash -euc '
                                    pnpm install --frozen-lockfile --store-dir /pnpm-store
                                    pnpm exec tsc --noEmit
                                    pnpm exec eslint .
                                    pnpm build
                                    pnpm test
                                '
                        '''
                    }
                }
            }
        }

        stage('Build images') {
            steps {
                sh '''
                    set -eu
                    $COMPOSE build
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -eu
                    # --remove-orphans so a service deleted from the compose file actually
                    # goes away, instead of surviving as a container nothing manages.
                    $COMPOSE up -d --remove-orphans
                    $COMPOSE ps
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    set -eu

                    # Checked from inside each container's network namespace rather than from
                    # the host. Jenkins runs in a container of its own, so its "localhost" is
                    # not the host's, and a published port proves nothing about the process
                    # behind it anyway. Joining the namespace tests the thing itself.
                    #
                    # /api/v1/health is readiness, not liveness: it answers 503 when it cannot
                    # reach the database, so a 200 here means the backend can actually serve.
                    backend_id=$($COMPOSE ps -q backend)
                    frontend_id=$($COMPOSE ps -q frontend)

                    echo "--> backend readiness"
                    docker run --rm --network "container:$backend_id" \
                        docker.io/curlimages/curl:latest \
                        -fsS --retry 60 --retry-delay 5 --retry-all-errors \
                        http://localhost:8000/api/v1/health

                    echo
                    echo "--> frontend serving"
                    docker run --rm --network "container:$frontend_id" \
                        docker.io/curlimages/curl:latest \
                        -fsS -o /dev/null -w 'HTTP %{http_code}\\n' \
                        --retry 60 --retry-delay 5 --retry-all-errors \
                        http://localhost:3000/
                '''
            }
        }
    }

    post {
        success {
            echo "Deployed. Frontend http://localhost:${FRONTEND_PORT}  API http://localhost:${BACKEND_PORT}/docs"
        }
        failure {
            // The logs of whatever did come up. A deploy that fails its smoke test leaves
            // the stack running on purpose: the container that will not start is the
            // evidence, and tearing it down here would delete it before anyone looked.
            sh '$COMPOSE ps || true'
            sh '$COMPOSE logs --tail 100 || true'
        }
        always {
            sh 'docker rm -f "$PG_CTR" >/dev/null 2>&1 || true'
        }
    }
}
