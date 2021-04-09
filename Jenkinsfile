node('python3 && garmin-connect && selenium') {
    checkout scm
    writeFile file: 'config.yaml', text: params.config
    if (params.retrieveActivities) {
        sh 'python3 garmin-connect-retrieval.py'
    }
    if (params.retrieveChallenges) {
        sh 'python3 challenge-scraper.py'
    }
}