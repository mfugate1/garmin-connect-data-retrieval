node('python3 && garmin-connect && selenium') {
    checkout scm
    writeFile file: 'config.yaml', text: params.config
    sh 'python3 garmin-connect-retrieval.py'
    sh 'python3 challenge-scraper.py'
}