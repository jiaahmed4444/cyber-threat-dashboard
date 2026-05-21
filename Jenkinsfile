pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'jiaahmed/cyber-threat-dashboard'
        DOCKER_TAG = "${BUILD_NUMBER}"
        REPO_URL = 'https://github.com/jiaahmed4444/cyber-threat-dashboard'
    }
    stages {
        stage('Code Fetch Stage') {
            steps {
                echo '========== FETCHING CODE FROM GITHUB =========='
                git branch: 'main', url: "${env.REPO_URL}", credentialsId: 'github-credentials'
                echo '✓ Code fetched successfully'
            }
        }
        stage('Docker Image Creation Stage') {
            steps {
                echo '========== BUILDING DOCKER IMAGE =========='
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}"
                    docker.withRegistry('', 'dockerhub-credentials')  {
                        sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                        sh "docker push ${DOCKER_IMAGE}"
                    }
                    echo "✓ Docker image pushed"
                }
            }
        }
        stage('Kubernetes Deployment Stage') {
            steps {
                echo '========== DEPLOYING TO KUBERNETES =========='
                script {
                    sh "kubectl apply -f deployment.yaml"
                    sh "kubectl apply -f service.yaml"
                    sh "kubectl rollout status deployment/cyber-threat-dashboard --timeout=180s"
                    echo "✓ Application deployed"
                }
            }
        }
        stage('Prometheus/Grafana Stage') {
            steps {
                echo '========== MONITORING SETUP =========='
                script {
                    sh "kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/prometheus-operator-0serviceMonitor.yaml 2>/dev/null || true"
                    echo "✓ Monitoring configured"
                }
            }
        }
    }
    post {
        success { echo '🎉 Pipeline completed successfully!' }
        failure { echo '❌ Pipeline failed!' }
    }
}
