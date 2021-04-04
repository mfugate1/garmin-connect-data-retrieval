node('python3 && garmin-connect') {
    writeFile file: 'config.yaml', text: params.config
    sh './garmin-connect-retrieval.py'
}