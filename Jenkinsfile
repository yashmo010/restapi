pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'python3 -m compileall -q app.py package.py'
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m unittest -v'
            }
        }

        stage('Package') {
            steps {
                sh 'python3 package.py'
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'dist/todo-api.zip', fingerprint: true
        }
    }
}
