
pipeline {
    agent any
 
    environment {
        IMAGE_REPO = "naim8855/flask-app"
        NETWORK_NAME = "myapp-network"
        VOLUME_NAME = "db-data"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        NGINX_CONF = "/root/flask-db-app/nginx/nginx.conf"
        STATE_FILE = "/root/flask-db-app/active_color.txt"
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
                sh '''
                    docker run --rm $IMAGE_REPO:$IMAGE_TAG python3 -m pytest test_app.py -v
                '''
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
 
        stage('Ensure Database Running') {
            steps {
                sh '''
                    if ! docker ps --format '{{.Names}}' | grep -q '^db-container$'; then
                        docker run -d \
                          --name db-container \
                          --network $NETWORK_NAME \
                          -e MYSQL_ROOT_PASSWORD=rootpass \
                          -e MYSQL_DATABASE=mydb \
                          -e MYSQL_USER=flaskuser \
                          -e MYSQL_PASSWORD=flaskpass \
                          -v $VOLUME_NAME:/var/lib/mysql \
                          mysql:8
                        for i in $(seq 1 20); do
                            docker exec db-container mysqladmin ping -uroot -prootpass --silent && break
                            sleep 3
                        done
                    else
                        echo "Database already running — skipping."
                    fi
                '''
            }
        }
 
        stage('Determine Active Color') {
            steps {
                script {
                    env.CURRENT_COLOR = sh(
                        script: "cat ${STATE_FILE} 2>/dev/null || echo blue",
                        returnStdout: true
                    ).trim()
                    env.NEW_COLOR = (env.CURRENT_COLOR == "blue") ? "green" : "blue"
                    echo "Current active: ${env.CURRENT_COLOR} — deploying new version as: ${env.NEW_COLOR}"
                }
            }
        }
 
        stage('Deploy New Color (alongside old)') {
            steps {
                sh '''
                    docker rm -f flask-$NEW_COLOR || true
                    docker run -d \
                      --name flask-$NEW_COLOR \
                      --network $NETWORK_NAME \
                      $IMAGE_REPO:$IMAGE_TAG
                '''
            }
        }
 
        stage('Health Check New Color') {
            steps {
                sh '''
                    for i in $(seq 1 10); do
                        if docker run --rm --network $NETWORK_NAME curlimages/curl:latest \
                          curl -sf http://flask-$NEW_COLOR:5000 > /dev/null; then
                            echo "flask-$NEW_COLOR is healthy."
                            break
                        fi
                        echo "Waiting for flask-$NEW_COLOR to become reachable... ($i/10)"
                        sleep 2
                    done
                '''
            }
        }
 
        stage('Switch Traffic to New Color') {
            steps {
                sh '''
                    sed -i "s/server flask-[a-z]*:5000;/server flask-$NEW_COLOR:5000;/" $NGINX_CONF
                    docker exec nginx-proxy nginx -s reload
                    echo -n "$NEW_COLOR" > $STATE_FILE
                '''
            }
        }
 
        stage('Remove Old Color') {
            steps {
                sh '''
                    docker rm -f flask-$CURRENT_COLOR || true
                '''
            }
        }
 
        stage('Final Verification') {
            steps {
                sh '''
                    for i in $(seq 1 10); do
                        if curl -sf http://localhost:5000 > /dev/null; then
                            echo "Verified — Nginx is correctly serving flask-$NEW_COLOR."
                            break
                        fi
                        echo "Waiting for Nginx to settle onto flask-$NEW_COLOR... ($i/10)"
                        sleep 2
                    done
                    curl -f http://localhost:5000
                    echo ""
                    echo "Zero-downtime deploy complete — live version is now: $NEW_COLOR"
                '''
            }
        }
    }
 
    post {
        success {
            echo "Pipeline succeeded — ${IMAGE_REPO}:${IMAGE_TAG} live as flask-${env.NEW_COLOR}, switched with zero downtime"
        }
        failure {
            echo 'Pipeline failed — old version was left running untouched, nothing was switched.'
        }
        always {
            sh 'docker logout || true'
        }
    }
}
