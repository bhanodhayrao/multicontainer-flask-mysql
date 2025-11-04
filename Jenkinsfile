pipeline {
  agent any
  options {
    skipDefaultCheckout(true)
    timestamps()
  }
  environment {
    // CHANGE THIS to your Docker Hub repo
    DOCKERHUB_REPO = 'yourhubuser/multicontainer-flask-mysql'
    DOCKERHUB_CREDENTIALS_ID = 'dockerhub-creds'
    // Build context & Dockerfile location (we keep Dockerfile inside app/)
    DOCKERFILE_PATH = 'app/Dockerfile'
    BUILD_CONTEXT   = 'app'
    APP_PORT        = '5000'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git rev-parse --short HEAD > .git_short'
      }
    }

    stage('Build image') {
      steps {
        script {
          env.GIT_SHORT = readFile('.git_short').trim()
        }
        sh '''
          set -eux
          docker build \
            -t "$DOCKERHUB_REPO:commit-$GIT_SHORT" \
            -t "$DOCKERHUB_REPO:latest" \
            -f "$DOCKERFILE_PATH" "$BUILD_CONTEXT"
        '''
      }
    }

    stage('Test container') {
      steps {
        sh '''
          set -eux
          # run app container in background
          docker run -d --rm --name ci_app -p 5000:5000 "$DOCKERHUB_REPO:commit-$GIT_SHORT"

          # simple wait-for app health: try for ~60s
          ok=0
          for i in $(seq 1 30); do
            if curl -fsS "http://localhost:${APP_PORT}/"; then ok=1; break; fi
            sleep 2
          done
          if [ "$ok" -ne 1 ]; then
            echo "App did not become ready in time. Logs:" >&2
            docker logs ci_app || true
            exit 1
          fi

          # hit the endpoints
          curl -fsS "http://localhost:${APP_PORT}/init"
          curl -fsS "http://localhost:${APP_PORT}/users"

          # cleanup
          docker rm -f ci_app
        '''
      }
      post {
        always {
          sh 'docker rm -f ci_app || true'
        }
      }
    }

    stage('Push to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                                          usernameVariable: 'DOCKERHUB_USER',
                                          passwordVariable: 'DOCKERHUB_PASS')]) {
          sh '''
            set -eux
            echo "$DOCKERHUB_PASS" | docker login -u "$DOCKERHUB_USER" --password-stdin
            docker push "$DOCKERHUB_REPO:commit-$GIT_SHORT"
            docker push "$DOCKERHUB_REPO:latest"
          '''
        }
      }
    }

    // OPTIONAL: uncomment to deploy on the same Jenkins host
    // stage('Deploy (optional)') {
    //   steps {
    //     sh '''
    //       set -eux
    //       docker rm -f prod_app || true
    //       docker pull "$DOCKERHUB_REPO:latest"
    //       docker run -d --name prod_app -p 5000:5000 "$DOCKERHUB_REPO:latest"
    //     '''
    //   }
    // }
  }

  post {
    always {
      // optional image cleanup to save space on agents
      sh '''
        docker image prune -f || true
      '''
    }
  }
}
