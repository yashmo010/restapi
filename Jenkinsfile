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
                script {
                    if (isUnix()) {
                        sh 'python3 -m compileall -q app.py package.py'
                    } else {
                        bat '"%PYTHON_EXE%" -m compileall -q app.py package.py'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m unittest -v'
                    } else {
                        bat '"%PYTHON_EXE%" -m unittest -v'
                    }
                }
            }
        }

        stage('Package') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 package.py'
                    } else {
                        bat '"%PYTHON_EXE%" package.py'
                    }
                }
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'dist/todo-api.zip', fingerprint: true
        }
    }
}
