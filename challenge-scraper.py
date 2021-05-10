#!/usr/bin/env python3

import pprint
import requests
import yaml

from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from utils.config import load_config
from time import sleep

def get_challenge_elements(driver):
    return driver.find_elements_by_xpath("//div[@class='current-challenge-placeholder']//div[@class='challenge-card']")

def wait_for_challenges(driver):
    wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='current-challenge-placeholder']//div[@class='challenge-card']")))

pp = pprint.PrettyPrinter(indent=4)

config = load_config()

for user in config['garmin_users']:
    try:
        chrome_opts = webdriver.ChromeOptions()
        chrome_opts.add_argument('--headless')
        chrome_opts.add_argument('--no-sandbox')
        chrome_opts.add_argument('start-maximized')
        chrome_opts.add_argument('--disable-dev-shm-usage')
        chrome_opts.add_argument('--window-size=1420,1080')

        driver = webdriver.Chrome(options=chrome_opts)

        print('Navigating to signin page')
        driver.get('https://connect.garmin.com/signin/')

        print('Waiting for login widget to be available')
        wait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'gauth-widget-frame-gauth-widget')))
        wait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))
        wait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password')))

        sleep(1)

        print('Entering username and password')
        driver.find_element_by_id('username').send_keys(user['username'])
        driver.find_element_by_id('password').send_keys(user['password'])

        print('Clicking submit')
        driver.find_element_by_id('login-btn-signin').click()
        wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/modern/challenge']")))

        print(f'Current URL: {driver.current_url}')
        print('Navigating to challenge page')
        driver.find_element_by_xpath("//a[@href='/modern/challenge']").click()
        wait_for_challenges(driver)

        print(f'Current URL: {driver.current_url}')

        challenges = []

        current_page = 1

        while True:
            # Get the total number of badges that we're going to scrape here
            # Can't just store the list of elements returned by this query because they'll be stale after we navigate to the details page and back
            print('Looking for challenges')
            challenge_count = len(get_challenge_elements(driver))
            print(f'Found {challenge_count} badges to gather')

            for i in range(challenge_count):
                # Navigate to the details page for this badge to collect challenge information
                print(f'Navigating to challenge {i}')
                get_challenge_elements(driver)[i].find_element_by_class_name('challenge-card-body').find_element_by_class_name('view-detail').click()
                wait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//h2[contains(@class, 'challenges_badgeChallengeName')]")))

                print(f'Current URL: {driver.current_url}')

                challenge = {'user': user['username'], 'url': driver.current_url}

                print('Getting the challenge name')
                challenge['name'] = driver.find_element_by_xpath("//h2[contains(@class, 'challenges_badgeChallengeName')]").text

                print('Getting the challenge rules')
                rules = driver.find_elements_by_xpath("//p[contains(@class, 'challenges_badgeChallengeRules')]")
                challenge['date_range'] = rules[0].text
                challenge['description'] = rules[1].text

                print('Getting the challenge image url')
                element = driver.find_element_by_xpath("//img[@role='presentation']")
                challenge['image_url'] = element.get_attribute('src')
                if not element.get_attribute('class').startswith('challenges_badgeNotAchieved'):
                    challenge['state'] = 'complete'

                print('Getting the challenge progress')
                # For challenges that haven't started yet, this won't exist. That's ok :)
                try:
                    challenge['progress_raw'] = driver.find_element_by_class_name('badge-progress-label').text
                except NoSuchElementException: 
                    pass

                challenges.append(challenge)

                print('Navigating back to main challenge page')
                driver.back()
                wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='current-challenge-placeholder']//div[@class='challenge-card']")))

                print(f'Current URL: {driver.current_url}')

                for i in range(current_page - 1):
                    driver.find_element_by_xpath('//a[@href="#" and @title="Next"]').click()
                    wait_for_challenges(driver)

            try:
                current_page = int(driver.find_element_by_id('current-page').get_attribute('value'))
                last_page = int(driver.find_element_by_xpath('//label[@for="current-page"]').text.split()[1])
            except NoSuchElementException:
                print('No pagination elements, collected all the available challenges')
                break

            if current_page != last_page:
                print(f'On page {current_page} of {last_page}, going to next page')
                driver.find_element_by_xpath('//a[@href="#" and @title="Next"]').click()
                wait_for_challenges(driver)
                current_page += 1
            else:
                print('On the last page, collected all the available challenges')
                break
                
            
    finally:
        driver.quit()

for challenge in challenges:
    dates = challenge['date_range'].split(' to ')
    challenge['start_date'] = datetime.strptime(dates[0], '%b %d, %Y')
    challenge['end_date'] = datetime.strptime(dates[1], '%b %d, %Y')

    if 'progress_raw' in challenge:
        challenge['type'] = 'cumulative'
        challenge['current_progress_display'] = challenge['progress_raw'].split(' / ')[0]
        challenge['current_progress'] = float(challenge['current_progress_display'].replace(',', ''))
        challenge['goal'] = float(challenge['progress_raw'].split(' / ')[1].split()[0].replace(',', ''))
        challenge['units'] = challenge['progress_raw'].split(' / ')[1].split()[1]
    elif 'Complete' in challenge['description'] or ' in one ' in challenge['description']:
        challenge['type'] = 'one_time_activity'
        desc_tokens = challenge['description'].split()
        for i, token in enumerate(desc_tokens):
            if token[:1].isdigit():
                if '-' in token:
                    challenge['goal'] = token.split('-')[0]
                    challenge['units'] = token.split('-')[1]
                else:
                    challenge['goal'] = token
                    challenge['units'] = desc_tokens[i + 1]
                break

    if 'state' not in challenge:
        if datetime.now() >= challenge['start_date'] and datetime.now() <= challenge['end_date']:
            challenge['state'] = 'active'
        else:
            challenge['state'] = 'inactive'

    challenge['start_date'] = datetime.strftime(challenge['start_date'], '%Y-%m-%d')
    challenge['end_date'] = datetime.strftime(challenge['end_date'], '%Y-%m-%d')

    for activity_type in ['run', 'cycling', 'walk', 'yoga', 'steps', 'strength']:
        if activity_type in challenge['description'].lower() or activity_type in challenge['name'].lower():
            challenge['activity_type'] = activity_type

    if 'activity_type' not in challenge:
        challenge['activity_type'] = 'unknown'

    if challenge['activity_type'] == 'run':
        challenge['icon'] = 'mdi:run'
        challenge['activity_type'] = 'running'
    elif challenge['activity_type'] == 'cycling':
        challenge['icon'] = 'mdi:bike'
    elif challenge['activity_type'] == 'walk':
        challenge['icon'] = 'mdi:walk'
        challenge['activity_type'] = 'walking'
    elif challenge['activity_type'] == 'yoga':
        challenge['icon'] = 'mdi:yoga'
    elif challenge['activity_type'] == 'steps':
        challenge['icon'] = 'mdi:shoe-print'
    elif challenge['activity_type'] == 'strength':
        challenge['icon'] = 'mdi:weight-lifter'

    if 'progress_raw' in challenge:
        challenge['current_progress'] = float(challenge['progress_raw'].split(' / ')[0].replace(',', ''))
        challenge['goal'] = float(challenge['progress_raw'].split(' / ')[1].split()[0].replace(',', ''))
        challenge['units'] = challenge['progress_raw'].split(' / ')[1].split()[1]

    # For one time activity challenges, if complete, set current_progress = goal
    if 'current_progress' not in challenge and challenge['state'] == 'complete':
        challenge['current_progress'] = challenge['goal']

print(f'Found {len(challenges)} challenges')
pp.pprint(challenges)

if 'homeassistant' in config and 'challenges_config' in config:
    sorted_challenges = []

    sorted_challenges += sorted([x for x in challenges if x['state'] != 'inactive'], key=lambda c: c['end_date'])
    sorted_challenges += [x for x in challenges if x['state'] == 'inactive']

    challenge_data = {}

    url = f'{config["homeassistant"]["url"]}/{config["challenges_config"]["homeassistant"]["webhook_prefix"]}'
    for i in range(config['challenges_config']['homeassistant']['count']):
        if i < len(sorted_challenges):
            requests.post(url + str(i + 1).zfill(2), json=sorted_challenges[i])
        else:
            requests.post(url + str(i + 1).zfill(2), json={'state': 'unknown'})
        