node('python3 && garmin-connect') {
    checkout scm
    writeFile file: 'config.yaml', text: params.config
    sh 'python3 garmin-connect-retrieval.py'
}