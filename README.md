# Multi-Container Flask + MySQL Application (with CI/CD using Jenkins, Docker, and GitHub)

## 🧩 Overview

This project demonstrates a **multi-container application** and a **CI/CD pipeline** integrating **Docker, GitHub, and Jenkins**.

It consists of:

* A **Flask web application** (Python)
* A **MySQL database**
* A **Docker Compose** setup to run both together
* A **Jenkins pipeline** for automated build, test, and deployment

---

## 📁 Project Structure

```
multicontainer-flask-mysql/
│
├── app/
│   ├── app.py              # Flask web application
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Flask app Dockerfile
│
├── docker-compose.yml      # Defines Flask + MySQL multi-container setup
├── Jenkinsfile             # CI/CD pipeline definition
└── README.md               # Project documentation
```

---

## ⚙️ Step 1: Multi-Container Setup (Docker Compose)

### Services

1. **web** – Flask app containerized from `app/Dockerfile`
2. **db** – MySQL 8.0 database container with environment variables

### Run Locally

```bash
docker-compose up --build
```

### Access the app

* Flask: [http://localhost:5000](http://localhost:5000)
* MySQL: port 3306 (internal access only)

### Verify network connectivity

Both containers share the same Docker network (created by Compose).
Run this to confirm:

```bash
docker network inspect multicontainer-app_default
```

---

## 🔁 Step 2: CI/CD Pipeline (Jenkins + Docker + GitHub)

### Workflow Summary

1. Jenkins automatically **clones the GitHub repository**.
2. Builds the **Docker image** for the Flask app.
3. Spins up a temporary **MySQL container** for testing.
4. Runs **integration tests**:

   * `/` endpoint
   * `/init` endpoint (creates & inserts sample data)
   * `/users` endpoint (verifies DB connection)
5. On success:

   * Pushes the Docker image to **Docker Hub**.
   * Tags images as:

     * `username/repo:latest`
     * `username/repo:commit-<short-sha>`

---

## 🧪 Jenkins Pipeline Stages

| Stage                  | Description                                      |
| ---------------------- | ------------------------------------------------ |
| **Checkout**           | Pulls code from GitHub                           |
| **Build Image**        | Builds Flask Docker image                        |
| **Test Container**     | Runs Flask + MySQL integration test using Docker |
| **Push to Docker Hub** | Pushes tested image to Docker Hub                |
| **(Optional) Deploy**  | Can pull and run the latest image on a server    |

---

## 🛠️ Environment Variables

| Variable              | Description                  |
| --------------------- | ---------------------------- |
| `MYSQL_ROOT_PASSWORD` | Root password for MySQL      |
| `MYSQL_DATABASE`      | Database name                |
| `MYSQL_USER`          | Database username            |
| `MYSQL_PASSWORD`      | Database user password       |
| `DB_HOST`             | Database service name (`db`) |

---

## 🧠 Example Endpoints

| Endpoint | Method | Description                         |
| -------- | ------ | ----------------------------------- |
| `/`      | GET    | Health check route                  |
| `/init`  | GET    | Creates table & inserts sample data |
| `/users` | GET    | Retrieves user list from MySQL      |

---

## 🚀 Deployment (Optional Stage)

You can add a `Deploy` stage in `Jenkinsfile` to auto-run the container:

```groovy
stage('Deploy') {
    steps {
        bat '''
            docker pull username/multicontainer-flask-mysql:latest
            docker rm -f flask-app || exit 0
            docker run -d --name flask-app -p 5000:5000 username/multicontainer-flask-mysql:latest
        '''
    }
}
```

---

## 📦 Docker Hub

Your built images are pushed to:

👉 [https://hub.docker.com/r/username/multicontainer-flask-mysql](https://hub.docker.com/r/username/multicontainer-flask-mysql)

---

## ✅ Final Results

✔️ `docker-compose up` runs Flask + MySQL
✔️ Jenkins automates build, test, and push
✔️ Docker Hub stores the versioned images
✔️ (Optional) Deploy stage can auto-run the image

---

## 👨‍💻 Author

**Your Name**
CI/CD Assignment – Multi-Container Web + Database Application
Technologies: *Python, Flask, MySQL, Docker, Jenkins, GitHub*
