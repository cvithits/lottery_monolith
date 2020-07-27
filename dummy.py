import base64
import datetime
import pickle
import sys
import os
import pandas as pd
import numpy as np
import requests
#from google.cloud import logging
#import chromedriver_binary

from google.cloud import storage
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup

PAGE_LOGGED_IN=0
PAGE_LOGIN_FORM=1
PAGE_UNKNOWN=2
SPREADSHEET_ID = '1SQPloXlYzjY4DgjBnIRgVIY6Y4026rUE9puEQQmXenU'
END_EPOCH = int(datetime.datetime.now().timestamp()*1000)
START_EPOCH = END_EPOCH-1 # uncomment this line for today data only
LOGIN_URL='https://www.lottovip.com/login'
GETDATA_URL='https://www.lottovip.com/member/result/all/[EPOCH]'
LOGGIN_USR='Blotto456'
LOGGIN_PW='Blotto456'
COOKIE_PATH='/tmp/lottery_cookie.pkl'
CHROMEDRIVER_PATH="/tmp/chromedriver"
DELAY=1


#sys.path.insert(0, CHROMEDRIVER_PATH)

def addToSheet(sheetName, df, sheetId=SPREADSHEET_ID):
     service = build('sheets', 'v4', credentials=None)
     sheet = service.spreadsheets()
     # Add sheet if not exists
     try:
          request_body = {'requests': [{'addSheet': { 'properties': {'title': str(sheetName)}}}]}
          response = sheet.batchUpdate(spreadsheetId=sheetId, body=request_body
          ).execute()
     except Exception as e:
          pass
    
     response = sheet.values().update(
          spreadsheetId=sheetId,
          valueInputOption='RAW',
          range="'"+sheetName+"'!"+'A1:D200',
          body=dict(
               majorDimension='ROWS',
               values=df.T.reset_index().T.values.tolist())
     ).execute()

def download_blob(bucket_name, source_blob_name, destination_file_name):
     storage_client = storage.Client()

     bucket = storage_client.bucket(bucket_name)
     blob = bucket.blob(source_blob_name)
     blob.download_to_filename(destination_file_name)


def upload_blob(bucket_name, source_file_name, destination_blob_name):
     storage_client = storage.Client()
     bucket = storage_client.bucket(bucket_name)
     blob = bucket.blob(destination_blob_name)

     blob.upload_from_filename(source_file_name)

def save_cookie(driver, path=COOKIE_PATH):
     pickle.dump( driver.get_cookies() , open(path,"wb"))

def load_cookie(driver, path=COOKIE_PATH):
     try:
          cookies = pickle.load(open(path, "rb"))
          for cookie in cookies:
               driver.add_cookie(cookie)
     except: #file not found
          pass

def Authenthicate(driver):
     currentPage=pageCheck(driver, PAGE_LOGGED_IN)

     if currentPage == PAGE_LOGGED_IN: # already logged-in
          return True
     elif currentPage == PAGE_LOGIN_FORM: # require re-login
          username = driver.find_element_by_name("username")
          username.send_keys(LOGGIN_USR)
          password = driver.find_element_by_name("password")
          password.send_keys(LOGGIN_PW)
          time.sleep(DELAY) # Delay needed
          password.send_keys(Keys.RETURN)
          
          currentPage=pageCheck(driver, PAGE_LOGGED_IN)
          if currentPage == PAGE_LOGGED_IN:
               save_cookie(driver)
               upload_blob("study_test1", "Lottery/cookie.pkl", COOKIE_PATH) # download lottery cookie
               return True
          else:
               return False

def pageCheck(driver, expectedPage):
     pageNo = expectedPage
     while pageNo < PAGE_UNKNOWN:
          try:
               if pageNo == PAGE_LOGIN_FORM:
                    WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.NAME, "password")))
                    return pageNo
                    break
               elif pageNo == PAGE_LOGGED_IN:
                    WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.XPATH, "//*[text()='"+LOGGIN_USR+"']")))
                    return pageNo
                    break
               else:
                    pageNo+=1
          except TimeoutException:
               pageNo+=1
     return PAGE_UNKNOWN

def extractData(dateStr, rawStr):
     soup = BeautifulSoup(rawStr, 'html.parser')
     items = soup.find_all(class_="card border-secondary text-center mb-2")
     tuple_list = list()
     
     for item in items:
          if len(tuple_list) >= (MAX_ROUND*2):
               break
          head_text = item.find_all(class_="card-header text-danger p-1")[0].get_text().replace("\n","").strip()
          body_titles = item.find_all(class_="card-header sub-card-header bg-transparent p-0")
          body_values = item.find_all(class_="card-text")  
          if len(body_titles) == len(body_values):
               for i in range(0, len(body_titles)):
                    digit_vals=parseDigit(body_values[i].get_text())
                    val=(head_text.replace(u"จับยี่กี VIP - รอบที่ ",""), digit_vals[0], digit_vals[1] , digit_vals[2])
                    if val not in tuple_list:
                         tuple_list.append(val)
          else:
               # somethings went wrong may be html page is updated.
               pass

     df = pd.DataFrame(tuple_list, columns=['Round', 'Digit3', 'Digit2', 'Digit1'])
     
     df.Digit3 = df.Digit3.astype(str)
     df.Digit2 = df.Digit2.astype(str)
     df.Digit1 = df.Digit1.astype(str)
     addToSheet(dateStr, df)

def getData(startEpoch=START_EPOCH, endEpoch=END_EPOCH):
     for epoch in range(START_EPOCH, END_EPOCH, ONEDAY_EPOCH):
          driver.get(GETDATA_URL.replace("[EPOCH]", str(epoch)))
          date_str=datetime.datetime.fromtimestamp(int(epoch/1000)).strftime("%Y%m%d")
          extractData(date_str, driver.page_source)


def fetch_data_requests(event=None, context=None):
     # only one day is allowed for now
     headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    
     s = requests.get(LOGIN_URL, headers=headers)
     print(s.status_code)
     #print(s.content)
     if s.status_code == 200:
          date_str=datetime.datetime.fromtimestamp(int(START_EPOCH/1000)).strftime("%Y%m%d")
          #extractData(date_str, s.content)
     else:
          pass # error handling here

def fetch_data_selenium(event, context):
     download_blob("study_test1", "Lottery/cookie.pkl", COOKIE_PATH) # download lottery cookie
     download_blob("study_test1", "chrome_driver/chromedriver", CHROMEDRIVER_PATH) # download chrome driver
     os.chmod(CHROMEDRIVER_PATH, 777)
     chrome_options = webdriver.ChromeOptions()
     chrome_options.add_argument('--no-sandbox')
     chrome_options.add_argument('--headless')
     chrome_options.add_argument('--disable-dev-shm-usage')
     chrome_options.add_argument('--disable-gpu')
     chrome_options.binary_location=CHROMEDRIVER_PATH
     driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=chrome_options)
     driver.get(LOGIN_URL)
     load_cookie(driver)
     if Authenthicate(driver):
          getData()
     else:
          pass #error handling here

fetch_data_requests()