import pickle
import datetime
STARTYEAR=2020
STARTMONTH=6
STARTDATE=18
START_EPOCH = int(datetime.datetime(STARTYEAR, STARTMONTH, STARTDATE, 0, 0).timestamp()*1000)
END_EPOCH = int(datetime.datetime.now().timestamp()*1000)
#START_EPOCH = END_EPOCH-1 # uncomment this line for today data only
ONEDAY_EPOCH=86400000
MAX_ROUND=30
HEADLESSMODE = False
LOGIN_URL='https://www.lottovip.com/login'
GETDATA_URL='https://www.lottovip.com/member/result/all/[EPOCH]'
COOKIE_PATH='cookie.pkl'
LOGGIN_USR='Blotto456'
LOGGIN_PW='Blotto456'

DELAY=2
PAGE_LOGIN_FORM=0
PAGE_LOGGED_IN=1
PAGE_UNKNOWN=2



def save_cookie(driver, path=COOKIE_PATH):
  pickle.dump( driver.get_cookies() , open(path,"wb"))

def load_cookie(driver, path=COOKIE_PATH):
    try:
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("yey")
    except: #file not found
        pass