from database import Database
import fitbit
import datetime
import pandas as pd



DATABASE_PATH = "name.db" # put the name of your database
db = Database(DATABASE_PATH)
all_users = db.get_all_users()
current_fitbit_client = 0

def refresh_cb(token):
    global current_fitbit_client
    access_token = token['access_token']
    refresh_token = token['refresh_token']
    expires_at = token['expires_at']
    db.update_tokens(current_fitbit_client, access_token, refresh_token, expires_at)
    print(token)

for user in all_users:

    phone = user.get('phone')
    user_chat_thread = user.get('chat_thread')
    current_fitbit_client = phone

    fitbit_details = db.get_fitbit_details(phone)
    user_id_fitbit = fitbit_details.get("user_id")

    user = db.get_user(phone)
    participant_id = user.get('participant_id')
    participant_name = user.get('participant_name')
    user_calorie_goal = user.get('calorie_goal')
    user_weight_goal = user.get('weight_goal')
    user_start_weight = user.get('start_weight')
    user_azm_goal = user.get('activity_zone')

    # FitBit
    fitbit_client = fitbit.Fitbit(
        client_id=fitbit_details.get('client_id'),
        client_secret=fitbit_details.get('client_secret'),
        access_token=fitbit_details.get('access_token'),
        refresh_token=fitbit_details.get('refresh_token'),
        expires_at=fitbit_details.get('expires_at'),
        refresh_cb=refresh_cb
    )

    # Get food and nutrition summary
    theday = datetime.date.today()
    start = theday - datetime.timedelta(days=14)
    dates = [start + datetime.timedelta(days=d) for d in range(14)]
    dates = [str(d) for d in dates]
    first_week_dates = dates[:7]
    second_week_dates = dates[7:14]
    weight_logs = {}

    ## First Week
    eaten = {}
    nutrition = {}
    for date in first_week_dates:
        url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/foods/log/date/' + date + '.json'
        response = fitbit_client.make_request(url)
        summary = response.get('summary')
        nutrition[date] = summary
        foods = response.get('foods')
        food_logs = []
        for food in foods:
            logged = food.get('loggedFood')
            food_logs.append(logged.get('name'))
        if len(food_logs) == 0:
            nutrition.pop(date, None)
        else:
            weight_logs[date] = {
                'eaten': food_logs
            }


    ## Second Week
    eaten = {}
    nutrition = {}
    for date in second_week_dates:
        url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/foods/log/date/' + date + '.json'
        response = fitbit_client.make_request(url)
        summary = response.get('summary')
        nutrition[date] = summary
        foods = response.get('foods')
        food_logs = []
        for food in foods:
            logged = food.get('loggedFood')
            food_logs.append(logged.get('name'))
        if len(food_logs) == 0:
            nutrition.pop(date, None)
        else:
            eaten[date] = food_logs

    # Get Weight logs
    ## First Week
    url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/body/log/weight/date/' + first_week_dates[0] + '/' + first_week_dates[6] + '.json'
    response = fitbit_client.make_request(url)
    response = response.get('weight')
    for log in response:
        bmi = log.get('bmi')
        weight = log.get('weight')
        date = log.get('date')
        weight_logs[date] = {
            'weight': weight
        }

    ## Second Week
    url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/body/log/weight/date/' + second_week_dates[0] + '/' + \
            second_week_dates[6] + '.json'
    response = fitbit_client.make_request(url)
    response = response.get('weight')
    for log in response:
        bmi = log.get('bmi')
        weight = log.get('weight')
        date = log.get('date')
        weight_logs[date] = {
            'weight': weight
        }
    phone = user.get("phone")

    # Get AZM
    ## First Week
    url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/activities/active-zone-minutes/date/' + first_week_dates[0] + '/' + first_week_dates[
        6] + '.json'
    response = fitbit_client.make_request(url)
    response = response.get('activities-active-zone-minutes')
    for log in response:
        activity = log.get('value')
        date = log.get('dateTime')
        azm = activity.get('activeZoneMinutes')
        weight_logs[date] = {
            'azm': azm
        }
        print(log)

    ## Second Week
    url = 'https://api.fitbit.com/1/user/' + user_id_fitbit + '/activities/active-zone-minutes/date/' + second_week_dates[
        0] + '/' + second_week_dates[
                6] + '.json'
    response = fitbit_client.make_request(url)
    response = response.get('activities-active-zone-minutes')
    for log in response:
        activity = log.get('value')
        azm_1w = activity.get('activeZoneMinutes')
        date = log.get('dateTime')
        weight_logs[date] = {
            'azm': azm_1w
        }
        print(log)


    df = pd.DataFrame(weight_logs,columns=dates)
    df.to_csv(phone+'_fitbit_data_'+str(dates[0]) +'_'+ str(dates[13])+'.csv')

