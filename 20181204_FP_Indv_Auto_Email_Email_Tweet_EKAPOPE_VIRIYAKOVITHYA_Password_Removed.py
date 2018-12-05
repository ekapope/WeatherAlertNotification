# -*- coding: utf-8 -*-
"""
This is a customize weather forcast alert (12 hours forecast from AccuWeather API)
It will send an email alert based on user setting (func_get_weather)

input: starts from line 20
output: tweet/ email notification

The function will execute the for loop starting from line 160

"""

import urllib
import urllib.parse
import json
import time
import pandas as pd
import logging
####################################################################################################
####################################################################################################
# Define % cutoff for probability of rain and snow 
rain_prob_cutoff = 20
snow_prob_cutoff = 20
# Setup the sleep time
SleepTime_hr = 1 # sleep time in hour
DelayTime_hr = 4 # delay time between email/tweet
####################################################################################################
####################################################################################################
## This function will do the following -
#1. send request to accuweather
#2. receive json file from accuweather
#3. convert the retrived json file to dataframe
#4. extract elements that we want, change the output table to html format and return variables tuple
def func_get_weather(url_page):

    json_page = urllib.request.urlopen(url_page)
    json_data = json.loads(json_page.read().decode())
    json_df = pd.DataFrame(json_data)
    
    # set maximum width, so the links are fully shown and clickable
    pd.set_option('display.max_colwidth', -1)
    json_df['Links'] = json_df['MobileLink'].apply(lambda x: '<a href='+x+'>Link</a>')
    
    json_df['Real Feel (degC)'] = json_df['RealFeelTemperature'].apply(lambda x: x.get('Value'))
    json_df['Weather'] = json_df['IconPhrase'] 
    json_df['% Rain'] = json_df['RainProbability'] 
    json_df['% Snow'] = json_df['SnowProbability'] 
    json_df[['Date','Time']] = json_df['DateTime'].str.split('T', expand=True)
    # trim the time to hh:mm format, change to str
    json_df[['Time']] = json_df['Time'].str.split('+', expand=True)[0].astype(str).str[:5]
    
    selected_df = json_df[['Date','Time','Real Feel (degC)','Weather',
                           '% Rain','% Snow','Links']]
    
    # dictionary of cell colors
    def color_negative_red(val):
        """
        Takes a scalar and returns a string with
        the css property `'color: red'` for negative
        strings, black otherwise.
        """
        color = 'red' if val > rain_prob_cutoff else 'black'
        return 'color: %s' % color
    
    data_html = selected_df.style.applymap(color_negative_red, subset=['% Rain', '% Snow']).set_properties(**{'text-align': 'center','font-family': 'Calibri'}).hide_index().render()
    current_retrieved_datetime = str(json_df['Date'][0])+' '+str(json_df['Time'][0])
    
    check_rain=""
    check_snow=""
    # check % rain column
    for i in range(0, len(json_df)):
        if json_df['% Rain'][i] > rain_prob_cutoff:
            check_rain= ", there is "+str(json_df['% Rain'][i])+"% chance of Rain @ "+str(json_df['Time'][i])
            break
    # check % snow column           
    for i in range(0, len(json_df)):
        if json_df['% Snow'][i] > snow_prob_cutoff:
            check_snow= ", there is "+str(json_df['% Snow'][i])+"% chance of Snow @ "+str(json_df['Time'][i])
            break
    
        
    alert_msg = check_rain +" "+check_snow
    if alert_msg == " ":
        alert_msg = "There will be no rain or snow in the next 12 hours."
        
    link_for_twitter = json_df['MobileLink'][0]
    
    return(data_html,current_retrieved_datetime,alert_msg,link_for_twitter)

####################################################################################################
## Send Email function
## 5 inputs: 
#1. fromAddr -> Your Gmail
#2. toAddr -> Recipient's email
#3. fromAddrPassword -> Your Gmail password
#4. Subject -> Email subject
#5. html -> Table in html formal attached to the email
## https://developers.google.com/gmail/api/quickstart/python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def func_SendMail(fromAddr,toAddr,fromAddrPassword,Subject,html):
    part2 = MIMEText(data_html, 'html')   
    msg = MIMEMultipart('alternative')

    msg.attach(part2)
   
    msg['Subject'] = Subject
    msg['From'] = fromAddr
    msg['To'] = ', '.join(toAddr) if type(toAddr) == list else toAddr
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(fromAddr, fromAddrPassword)
        server.sendmail(fromAddr, toAddr, msg.as_string())
        server.quit()
        print('E-mail Sent to ',toAddr)  
    except:
        print ("Error: unable to send email ",toAddr)
    return (1) # check if successful
####################################################################################################
# Tweet function
# This will tweet the tweet_msg
link_for_twitter = ''
def main_tweet(tweet_msg):
    api = tweepy.API(auth)
    api.update_status(status=tweet_msg)
    return(print('successful tweet!'))
####################################################################################################
####################################################################################################
# Email Setup
SenderGmailAddr = 'your_email@gmail.com' # Your Gmail
SenderGmailPassword = 'password' #Your Gmail password
Recipients   = ['Recipient1@xxx','Recipient1@xxx'] # Recipient's email (send to)
####################################################################################################
# https://medium.freecodecamp.org/creating-a-twitter-bot-in-python-with-tweepy-ac524157a607
import tweepy
# Twitter Setup, using the keys obtained from twitter API
consumer_key = 'your_twitter_key'
consumer_secret = 'your_twitter_key'
access_token = 'your_twitter_key'
access_token_secret = 'your_twitter_key'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
####################################################################################################
# Get Weather
location = "135564" # Lille
myapikey= "your_accuweather_API_key"
url_page = "http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/"+str(location)+"?apikey="+myapikey+"&details=true&metric=true"
####################################################################################################
# Setup # of loops and sleep delay time
num_repeat = 999 # number of loops to repeat
previous_alert_msg = "" # initialize alert msg
Sleeptime = 60*60*SleepTime_hr # sleep time in seconds 60*60 = 1 hr
delay_time = 60*60*DelayTime_hr # delay time if execute
####################################################################################################
####################################################################################################
# Execute functions, retrieve data and send email+tweet
for i in range(num_repeat):

    time_old = ''
    try:
        data_html,current_retrieved_datetime,alert_msg,link_for_twitter = func_get_weather(url_page)
    except (RuntimeError, TypeError, NameError, ValueError, urllib.error.URLError):
        print('error catched')

# check if there is any changes in weather, if no changes, do nothing
    if len(alert_msg) > 0 and previous_alert_msg == alert_msg:
        print(i, current_retrieved_datetime, 'no changes in weather forecast')
        
    if len(alert_msg) > 0 and previous_alert_msg != alert_msg:
####### Tweet        
        previous_alert_msg= alert_msg               
        tweet_msg  = current_retrieved_datetime+' '+'12-hr Weather Forecast' +' - '+ alert_msg +' '+link_for_twitter
        main_tweet(tweet_msg)
####### Send email
        fromAddr = SenderGmailAddr 
        fromAddrPassword = SenderGmailPassword
        toAddr   = Recipients 
        Subject  = current_retrieved_datetime+' '+'12-hr Weather Forecast'+' - '+ alert_msg
        response = func_SendMail(fromAddr,toAddr,fromAddrPassword,Subject,data_html)
        print(i, current_retrieved_datetime, response)
        time.sleep(delay_time)
#https://stackoverflow.com/questions/2513479/redirect-prints-to-log-file/2513766
#https://docs.python.org/2/howto/logging.html        
#https://docs.python.org/3/library/logging.html
#logging the events
    if __name__ == "__main__":
        logging.basicConfig(level=logging.DEBUG, filename="FP_logfile", filemode="a+",
                            format="%(asctime)-15s %(levelname)-8s %(message)s")
        logging.info(Subject)
        logging.info(tweet_msg)
                          
    time.sleep(Sleeptime)
    
print(current_retrieved_datetime,'Run Completed')

