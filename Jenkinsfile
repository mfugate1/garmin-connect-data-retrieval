node('python3 && garmin-connect') {
    checkout scm
    writeFile file: 'config.yaml', text: params.config
    sh './garmin-connect-retrieval.py'
}