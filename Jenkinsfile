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

      # ----- Config -----
      $ciNet     = "ci_net_$env:BUILD_NUMBER"
      $dbName    = "flaskdb"
      $dbUser    = "flaskuser"
      $dbPass    = "flaskpass"
      $hostPort  = 5001
      $imageTag  = "$($env:DOCKERHUB_REPO):commit-$($env:GIT_SHORT)"

      function ContainerExists($name) {
        $id = (docker ps -a -q -f "name=$name").Trim()
        return -not [string]::IsNullOrEmpty($id)
      }

      function DumpLogs {
        Write-Host "==== ci_app logs ===="
        if (ContainerExists "ci_app") {
          docker logs ci_app 2>$null | Out-String | Write-Host
        } else {
          Write-Host "(no ci_app container)"
        }
        Write-Host "==== ci_db logs ===="
        if (ContainerExists "ci_db") {
          docker logs ci_db 2>$null | Out-String | Write-Host
        } else {
          Write-Host "(no ci_db container)"
        }
      }

      function FailWithLogs($msg) {
        DumpLogs
        throw $msg
      }

      Write-Host "1) Create temp network: $ciNet"
      docker network create $ciNet | Out-Null

      try {
        Write-Host "2) Start MySQL sidecar (alias=db)"
        docker run -d --rm --name ci_db --network $ciNet --network-alias db `
          -e MYSQL_ROOT_PASSWORD=rootpass123 `
          -e MYSQL_DATABASE=$dbName `
          -e MYSQL_USER=$dbUser `
          -e MYSQL_PASSWORD=$dbPass `
          mysql:8.0 | Out-Null

        Write-Host "3) Wait for MySQL to be ready (mysqladmin ping)"
        $dbReady = $false
        for ($i=1; $i -le 90; $i++) {
          docker exec ci_db mysqladmin ping -h 127.0.0.1 -u$dbUser -p$dbPass --silent
          if ($LASTEXITCODE -eq 0) { $dbReady = $true; break }
          Start-Sleep -Seconds 2
        }
        if (-not $dbReady) { FailWithLogs "DB not ready after waiting." }

        Write-Host "3b) Verify SQL auth & schema with SELECT 1 (arg-array to avoid quoting issues)"
        $args = @("mysql", "-h", "127.0.0.1", "-u$dbUser", "-p$dbPass", "-D", "$dbName", "-e", "SELECT 1;")
        $sqlOK = $false
        for ($i=1; $i -le 30; $i++) {
          docker exec ci_db @args | Out-Null
          if ($LASTEXITCODE -eq 0) { $sqlOK = $true; break }
          Start-Sleep -Seconds 2
        }
        if (-not $sqlOK) { FailWithLogs "DB auth/schema check failed for $dbUser@$dbName." }

        # Small extra cushion
        Start-Sleep -Seconds 4

        Write-Host "4) Run app on same network with image: $imageTag (host port $hostPort)"
        docker run -d --rm --name ci_app --network $ciNet -p ${hostPort}:5000 `
          -e DB_HOST=db `
          -e MYSQL_DATABASE=$dbName `
          -e MYSQL_USER=$dbUser `
          -e MYSQL_PASSWORD=$dbPass `
          "$imageTag" | Out-Null

        # Sanity: confirm app container exists
        if (-not (ContainerExists "ci_app")) {
          FailWithLogs "App container did not start."
        }

        Write-Host "5) Wait for app root '/' to return 200"
        $appReady = $false
        for ($i=1; $i -le 60; $i++) {
          & curl.exe --fail --silent --show-error "http://localhost:${hostPort}/" | Out-Null
          if ($LASTEXITCODE -eq 0) { $appReady = $true; break }
          Start-Sleep -Seconds 2
        }
        if (-not $appReady) { FailWithLogs "App root (/) never became healthy." }

        # Extra cushion before DB-using endpoints
        Start-Sleep -Seconds 5

        Write-Host "6) Hit /init with retries (DB create + insert)"
        $ok = $false
        for ($i=1; $i -le 30; $i++) {
          & curl.exe --fail --silent --show-error "http://localhost:${hostPort}/init" | Out-Null
          if ($LASTEXITCODE -eq 0) { $ok = $true; break }
          Start-Sleep -Seconds 3
        }
        if (-not $ok) { FailWithLogs "/init failed after retries." }

        Write-Host "7) Hit /users with retries (ensure query works)"
        $ok = $false
        $resp = ""
        for ($i=1; $i -le 30; $i++) {
          $resp = & curl.exe --fail --silent --show-error "http://localhost:${hostPort}/users"
          if ($LASTEXITCODE -eq 0 -and $resp) { $ok = $true; break }
          Start-Sleep -Seconds 3
        }
        if (-not $ok) { FailWithLogs "/users failed after retries." }

        Write-Host "Users response: $resp"
        Write-Host "All integration checks passed ✅"
      }
      catch {
        Write-Host "Caught exception in test stage:"
        Write-Host $_.Exception.Message
        DumpLogs
        throw
      }
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
