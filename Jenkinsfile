pipeline {
  agent any
  options {
    skipDefaultCheckout(true)
    timestamps()
  }
  environment {
    // TODO: change to your Docker Hub repo
    DOCKERHUB_REPO = 'bhanodhayrao/multicontainer-flask-mysql'
    DOCKERHUB_CREDENTIALS_ID = 'dockerhub-creds'
    DOCKERFILE_PATH = 'app/Dockerfile'
    BUILD_CONTEXT   = 'app'
    APP_PORT        = '5000'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        // write short git sha to a file (Windows)
        bat 'git rev-parse --short HEAD > .git_short'
        script {
          env.GIT_SHORT = readFile('.git_short').trim()
          echo "Commit short SHA: ${env.GIT_SHORT}"
        }
      }
    }

    stage('Build image') {
      steps {
        bat """
        echo Building %DOCKERHUB_REPO%:commit-%GIT_SHORT% and :latest
        docker build ^
          -t "%DOCKERHUB_REPO%:commit-%GIT_SHORT%" ^
          -t "%DOCKERHUB_REPO%:latest" ^
          -f "%DOCKERFILE_PATH%" "%BUILD_CONTEXT%"
        """
      }
    }

        stage('Test container') {
      steps {
        bat """
        @echo on
        set CI_NET=ci_net_%BUILD_NUMBER%

        REM 1) Create a temp network
        docker network create %CI_NET%

        REM 2) Start MySQL sidecar on that network with alias 'db'
        docker run -d --rm --name ci_db --network %CI_NET% --network-alias db ^
          -e MYSQL_ROOT_PASSWORD=rootpass123 ^
          -e MYSQL_DATABASE=flaskdb ^
          -e MYSQL_USER=flaskuser ^
          -e MYSQL_PASSWORD=flaskpass ^
          mysql:8.0

        REM 3) Wait for MySQL to be ready (up to ~60s)
        set ok=0
        for /L %%i in (1,1,30) do (
          docker exec ci_db mysqladmin ping -h localhost -uflaskuser -pflaskpass --silent >NUL 2>&1 && (set ok=1 & goto :dbready)
          timeout /t 2 >NUL
        )
        :dbready
        if %ok% NEQ 1 (
          echo MySQL did not become ready in time. DB logs:
          docker logs ci_db
          exit /b 1
        )

        REM 4) Run the app on same network, mapping host 5001->container 5000 to avoid conflicts
        docker run -d --rm --name ci_app --network %CI_NET% -p 5001:5000 ^
          -e DB_HOST=db ^
          -e MYSQL_DATABASE=flaskdb ^
          -e MYSQL_USER=flaskuser ^
          -e MYSQL_PASSWORD=flaskpass ^
          "%DOCKERHUB_REPO%:commit-%GIT_SHORT%"

        REM 5) Wait for app to come up and exercise endpoints
        set ok=0
        for /L %%i in (1,1,30) do (
          curl -fsS http://localhost:5001/ >NUL 2>&1 && (set ok=1 & goto :appready)
          timeout /t 2 >NUL
        )
        :appready
        if %ok% NEQ 1 (
          echo App did not become ready. Showing logs...
          docker logs ci_app
          exit /b 1
        )

        curl -fsS http://localhost:5001/init >NUL
        curl -fsS http://localhost:5001/users >NUL
        """
      }
      post {
        always {
          bat """
          docker rm -f ci_app 2>NUL || exit /b 0
          docker rm -f ci_db 2>NUL || exit /b 0
          docker network rm ci_net_%BUILD_NUMBER% 2>NUL || exit /b 0
          """
        }
      }
    }


    stage('Push to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                                          usernameVariable: 'DOCKERHUB_USER',
                                          passwordVariable: 'DOCKERHUB_PASS')]) {
          bat """
          echo Logging into Docker Hub as %DOCKERHUB_USER%
          echo %DOCKERHUB_PASS% | docker login -u "%DOCKERHUB_USER%" --password-stdin

          docker push "%DOCKERHUB_REPO%:commit-%GIT_SHORT%"
          docker push "%DOCKERHUB_REPO%:latest"
          """
        }
      }
    }

    // OPTIONAL: uncomment to deploy on the Jenkins Windows host
    // stage('Deploy (optional)') {
    //   steps {
    //     bat """
    //     docker rm -f prod_app 2>NUL || exit /b 0
    //     docker pull "%DOCKERHUB_REPO%:latest"
    //     docker run -d --name prod_app -p 5000:5000 "%DOCKERHUB_REPO%:latest"
    //     """
    //   }
    // }
  }

  post {
    always {
      // best-effort clean up of dangling images
      bat 'docker image prune -f || exit /b 0'
    }
  }
}
