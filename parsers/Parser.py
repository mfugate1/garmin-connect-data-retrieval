def parse_activity_to_row(activity, config, user):
    row = parse_row(activity, config, user)
    row['activityType'] = activity['activityType']['typeKey']
    return row

def parse_row(item, config, user):
    row = {'user': user}
    for key, value in item.items():
        if key in config['fields']:
            k = key
            v = value
            if config['fields'][key] is not None and 'units' in config['fields'][key]:
                k = f"{key}_{config['fields'][key]['units'].replace(' ', '_')}"
            if config['fields'][key] is not None and value is not None and 'transform' in config['fields'][key]:
                try:
                    v = eval(config['fields'][key]['transform'])
                except ZeroDivisionError as ex:
                    print(f'WARNING - Divide by zero error when transforming {key}. Value will remain as {value}')
            row[k] = v
    return row