import pandas as pd
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import os

test_date = datetime.datetime(2016, 6, 12)
milo_deplatform_date = datetime.datetime(2016, 7, 19)
outdir = ".//data/out"
tempdir = ".//data/temp"

def convert_dates(data):
    '''
    converts dates to datetime object
    '''
    # convert to datetime object
    data['created_at'] = pd.to_datetime(data['created_at'])
    # don't localize time
    data['created_at'] = data['created_at'].dt.tz_localize(None) 

    # reset hour, min, sec to 0
    data['created_at'] = data['created_at'].apply(
        lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))

    return data

def count_days(date, deplatform_date):
    '''
    helper function to count number of days since deplatform date
    '''
    return date - deplatform_date

def user_activity_levels(data, deplatform_date):
    '''
    measures posting activity levels by counting the number of tweets
    that occur per each time window (1 day)
    '''
    groupedUsers = data[['created_at', 'text']].groupby(by='created_at')

    num_tweets = groupedUsers.count()['text'] # number of tweets per time window

    df = num_tweets.reset_index().rename(
        columns={"created_at": "Date", "text": "# Tweets"})

    df['Date'] = df['Date'].apply(
        lambda x: count_days(x, deplatform_date)).dt.days

    # convert df to csv
    out_path = os.path.join(tempdir, "userActivityLevels.csv")
    df.to_csv(out_path)

    return df

def num_unique_users(data, deplatform_date):
    '''
    measures number of unique users who posted during 
    each time window (1 day)
    '''
    groupedUsers = data[['created_at', 'author_id']].groupby(by='created_at')

    date_ix = []
    numUniqueUsers_ix = []
    for date, authors in groupedUsers:
        uniqueUsers = set(authors['author_id']) # set of unique users
        
        date_ix.append(date)
        numUniqueUsers_ix.append(len(uniqueUsers))

    df = pd.DataFrame(data={
        "Date": date_ix, "# Unique Users": numUniqueUsers_ix})

    df['Date'] = df['Date'].apply(
        lambda x: count_days(x, deplatform_date)).dt.days

    # convert df to csv
    out_path = os.path.join(tempdir, "uniqueUsers.csv")
    df.to_csv(out_path)

    return df

def new_users_count(data, deplatform_date):
    '''
    counts the number of new users per time window (1 day)
    after an initial 7 day period of not counting new users (seenUsers)
    '''
    dates_sorted = data['created_at'].sort_values().reset_index(drop=True)
    start_date = dates_sorted[0]
    end_date = start_date + datetime.timedelta(days=7)
    seen_df = data[data['created_at'] < end_date].reset_index()
    # set of all users who posted in 7 day period
    seenUsers = set(seen_df['author_id'].unique())

    # all users after 7th day since start date aka on 8th day
    new_users_df = data[data['created_at'] > end_date]
    groupedUsers = new_users_df[['created_at', 'author_id']].groupby(by='created_at')

    date_ix = []
    numNewUsers_ix = []
    for date, authors in groupedUsers:
        groupUsers = set(authors['author_id'])
        newUsers = groupUsers - seenUsers # newUsers for date

        date_ix.append(date)
        numNewUsers_ix.append(len(newUsers))

        # update seenUsers 
        seenUsers = seenUsers.union(newUsers)

    newUsers_df = pd.DataFrame(data={
        'Date': date_ix, '# New Users': numNewUsers_ix})

    newUsers_df['Date'] = newUsers_df['Date'].apply(
        lambda x: count_days(x, deplatform_date)).dt.days

    # convert df to csv
    out_path = os.path.join(tempdir, "newUsers.csv")
    newUsers_df.to_csv(out_path)

    return newUsers_df

# functions used to create line charts

def create_newUsers_graph(df):
    '''
    creates graph for new users
    '''
    sns.lineplot(data=df, x='Date', y="# New Users")
    plt.xlabel('# Days Before and After Deplatforming')
    plt.title("Number of New Users")

    out_path = os.path.join(outdir, "newUsersPlot.png")
    plt.savefig(out_path, bbox_inches='tight')

def create_uniqueUsers_graph(df):
    '''
    creates graph for unique users
    '''
    sns.lineplot(data=df, x="Date", y="# Unique Users")
    plt.xlabel('# Days Before and After Deplatforming')
    plt.title("Number of Unique Users")

    out_path = os.path.join(outdir, "uniqueUsersPlot.png")
    plt.savefig(out_path, bbox_inches='tight')

def create_userActivity_graph(df):
    '''
    creates graph for user activity
    '''
    sns.lineplot(data=df, x="Date", y="# Tweets")
    plt.xlabel('# Days Before and After Deplatforming')
    plt.title("Volume of Tweets")

    out_path = os.path.join(outdir, "userActivityPlot.png")
    plt.savefig(out_path, bbox_inches='tight')

def numOfTweets(df, deplatform_date):
    '''
    calculates number of tweets before and after deplatforming
    '''
    if deplatform_date == 0:
        before_deplat_df = df[df['Date'] < deplatform_date]
        after_deplat_df = df[df['Date'] > deplatform_date]
    else: 
        before_deplat_df = df[df['created_at'] < deplatform_date]
        after_deplat_df = df[df['created_at'] > deplatform_date]

    num_df = pd.DataFrame(data={"Before": [len(before_deplat_df)], "After": [len(after_deplat_df)]})

    return num_df

def aggregate_twitter_vals():
    '''
    gets total for both before and after deplatform date
    '''
    newUsers_df = pd.read_csv(os.path.join(tempdir, "newUsers.csv"))
    uniqueUsers_df = pd.read_csv(os.path.join(tempdir, "uniqueUsers.csv"))
    userActivity_df = pd.read_csv(os.path.join(tempdir, "userActivityLevels.csv"))

    numOfTweets(newUsers_df, 0).to_csv(os.path.join(outdir, "newUsers_totals.csv"))
    numOfTweets(uniqueUsers_df, 0).to_csv(os.path.join(outdir, "uniqueUsers_totals.csv"))
    numOfTweets(userActivity_df, 0).to_csv(os.path.join(outdir, "userActivity_totals.csv"))

# main function 

def calculate_stats(data, test=False):
    df = convert_dates(data)

    if test == False:
        # create csvs out of data
        userActivity_df = user_activity_levels(df, milo_deplatform_date)
        uniqueUsers_df = num_unique_users(df, milo_deplatform_date)
        newUsers_df = new_users_count(df,milo_deplatform_date)
        # counts number of tweets before and after deplatforming 
        totalTweets = numOfTweets(df, milo_deplatform_date)
    else:
        userActivity_df = user_activity_levels(df, test_date)
        uniqueUsers_df = num_unique_users(df, test_date)
        newUsers_df = new_users_count(df,test_date)
        totalTweets = numOfTweets(df, test_date)

    out_path = os.path.join(outdir, "numOfTweetsBefAft.csv")
    totalTweets.to_csv(out_path)
    aggregate_twitter_vals()

    # create graphs + save as pngs
    create_newUsers_graph(newUsers_df)
    plt.clf() # clear plot
    create_uniqueUsers_graph(uniqueUsers_df)
    plt.clf()
    create_userActivity_graph(userActivity_df)

