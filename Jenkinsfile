pipeline {
    agent any

    environment {
        IMAGE_REPO = "naim8855/flask-app"
        NETWORK_NAME = "myapp-network"
        VOLUME_NAME = "db-data"
        // BUILD_NUMBER is a built-in Jenkins variable — auto-increments every run: v1, v2, v3...
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                dir('flask-app') {
                    sh '''
                        docker build -t $IMAGE_REPO:$IMAGE_TAG -t $IMAGE_REPO:latest .
                    '''
                }
            }
        }

        stage('Run Tests') {
    steps {
        dir('flask-app') {
            sh '''
                docker run --rm $IMAGE_REPO:$IMAGE_TAG python3 -m pytest test_app.py -v
            '''
        }
    }
}
        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                }
            }
        }

        stage('Push Image') {
            steps {
                sh '''
                    docker push $IMAGE_REPO:$IMAGE_TAG
                    docker push $IMAGE_REPO:latest
                '''
            }
        }

        stage('Ensure Network Exists') {
            steps {
                sh '''
                    docker network inspect $NETWORK_NAME >/dev/null 2>&1 || \
                    docker network create $NETWORK_NAME
                '''
            }
        }

        stage('Ensure Volume Exists') {
            steps {
                sh '''
                    docker volume inspect $VOLUME_NAME >/dev/null 2>&1 || \
                    docker volume create $VOLUME_NAME
                '''
            }
        }

        stage('Start Database') {
            steps {
                sh '''
                    docker rm -f db-container || true
                    docker run -d \
                      --name db-container \
                      --network $NETWORK_NAME \
                      -e MYSQL_ROOT_PASSWORD=rootpass \
                      -e MYSQL_DATABASE=mydb \
                      -e MYSQL_USER=flaskuser \
                      -e MYSQL_PASSWORD=flaskpass \
                      -v $VOLUME_NAME:/var/lib/mysql \
                      mysql:8
                '''
            }
        }

        stage('Wait for Database') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        docker exec db-container mysqladmin ping -uroot -prootpass --silent && break
                        echo "Waiting for MySQL..."
                        sleep 3
                    done
                '''
            }
        }

        stage('Deploy Flask App') {
            steps {
                sh '''
                    docker rm -f flask-container || true
                    docker run -d \
                      --name flask-container \
                      --network $NETWORK_NAME \
                      -p 5000:5000 \
                      $IMAGE_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    sleep 5
                    curl -f http://localhost:5000
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded — deployed ${IMAGE_REPO}:${IMAGE_TAG}, also pushed as :latest"
        }
        failure {
            echo 'Pipeline failed — check the stage logs above.'
        }
        always {
            sh 'docker logout || true'
        }
    }
}
