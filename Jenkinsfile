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
        powershell(returnStatus: false, script: '''
          $ErrorActionPreference = "Stop"
          $env:CI_NET = "ci_net_$env:BUILD_NUMBER"

          Write-Host "1) Create temp network: $env:CI_NET"
          docker network create $env:CI_NET | Out-Null

          Write-Host "2) Start MySQL sidecar (alias=db)"
          docker run -d --rm --name ci_db --network $env:CI_NET --network-alias db `
            -e MYSQL_ROOT_PASSWORD=rootpass123 `
            -e MYSQL_DATABASE=flaskdb `
            -e MYSQL_USER=flaskuser `
            -e MYSQL_PASSWORD=flaskpass `
            mysql:8.0 | Out-Null

          Write-Host "3) Wait for MySQL to be ready"
          $ok = $false
          for ($i=1; $i -le 30; $i++) {
            docker exec ci_db mysqladmin ping -h localhost -uflaskuser -pflaskpass --silent
            if ($LASTEXITCODE -eq 0) { $ok = $true; break }
            Start-Sleep -Seconds 2
          }
          if (-not $ok) {
            Write-Host "MySQL did not become ready in time. Logs:"
            docker logs ci_db
            throw "DB not ready"
          }

          Write-Host "4) Run app on same network, expose host 5001"
          docker run -d --rm --name ci_app --network $env:CI_NET -p 5001:5000 `
            -e DB_HOST=db `
            -e MYSQL_DATABASE=flaskdb `
            -e MYSQL_USER=flaskuser `
            -e MYSQL_PASSWORD=flaskpass `
            "$env:DOCKERHUB_REPO:commit-$env:GIT_SHORT" | Out-Null

          Write-Host "5) Wait for app and hit endpoints"
          $ok = $false
          for ($i=1; $i -le 30; $i++) {
            curl -fsS "http://localhost:5001/" | Out-Null
            if ($LASTEXITCODE -eq 0) { $ok = $true; break }
            Start-Sleep -Seconds 2
          }
          if (-not $ok) {
            Write-Host "App did not become ready. Logs:"
            docker logs ci_app
            throw "App not ready"
          }

          curl -fsS "http://localhost:5001/init"  | Out-Null
          curl -fsS "http://localhost:5001/users" | Out-Null
        ''')
      }
      post {
        always {
          powershell '''
            docker rm -f ci_app 2>$null | Out-Null
            docker rm -f ci_db  2>$null | Out-Null
            docker network rm "ci_net_$env:BUILD_NUMBER" 2>$null | Out-Null
          '''
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
