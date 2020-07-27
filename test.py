# -*- coding: utf-8 -*-
import time
import sys
import pandas as pd
import numpy as np
import exportToGoogleSheet as expGSheet
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from config import *
from bs4 import BeautifulSoup
chrome_options = webdriver.ChromeOptions()
if HEADLESSMODE: chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome('G:\Programs\chromedriver',chrome_options=chrome_options)

pageTravList=[]

#pageNo = assumed current page
def pageCheck(pageList, expectedPage):
    pageNo = expectedPage
    while pageNo < PAGE_UNKNOWN:
        try:
            if pageNo == PAGE_LOGIN_FORM:
                WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.NAME, "password")))
                break
            elif pageNo == PAGE_LOGGED_IN:
                WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.XPATH, "//*[text()='"+LOGGIN_USR+"']")))
                break
            else:
                pageNo+=1
        except TimeoutException:
            pageNo+=1
    pageTravList.append(pageNo)

    return (pageNo == expectedPage)

def Authenthicate(pageTravList):
    isSuccess = False
    if pageCheck(pageTravList[:-1], PAGE_LOGIN_FORM):
        username = driver.find_element_by_name("username")
        username.send_keys(LOGGIN_USR)
        password = driver.find_element_by_name("password")
        password.send_keys(LOGGIN_PW)
        time.sleep(DELAY) # Delay needed
        password.send_keys(Keys.RETURN)
        
        if pageCheck(pageTravList[:-1], PAGE_LOGGED_IN):
            isSuccess= True

    elif pageCheck(pageTravList[:-1], PAGE_LOGGED_IN):
        isSuccess = True
    
    driver.get_screenshot_as_file("Authenthicate.png")
    return isSuccess



def getData(pageTravList, startEpoch=START_EPOCH, endEpoch=END_EPOCH):
    for epoch in range(START_EPOCH, END_EPOCH, ONEDAY_EPOCH):
        print(GETDATA_URL.replace("[EPOCH]", str(epoch)))
        driver.get(GETDATA_URL.replace("[EPOCH]", str(epoch)))
        date_str=datetime.datetime.fromtimestamp(int(epoch/1000)).strftime("%Y%m%d")
        #time.sleep(DELAY)
        extractData(date_str)
        driver.get_screenshot_as_file(date_str+".png")
    return True

def parseDigit(value):
    vals=["","",""]
    for i in range( min(len(vals), len(value)) ):
        if len(value) == 2:
            vals[i+1]=value[i]
        elif len(value) == 3:
            vals[i]=value[i]
        else:
            break
    return vals

def extractData(dateStr):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.find_all(class_="card border-secondary text-center mb-2")
    tuple_list = list()
    #step1
    for item in items:
        if len(tuple_list) >= (MAX_ROUND*2):
            break
        head_text = item.find_all(class_="card-header text-danger p-1")[0].get_text().replace("\n","").strip()
        #body = item.find_all(class_="card text-center w-50 border-card-right m-0")
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

    df_ori = pd.DataFrame(tuple_list, columns=['Round', 'Digit3', 'Digit2', 'Digit1'])
    
    df_ori.Digit3 = df_ori.Digit3.astype(str)
    df_ori.Digit2 = df_ori.Digit2.astype(str)
    df_ori.Digit1 = df_ori.Digit1.astype(str)
    expGSheet.Export_Data_To_Sheets(df_ori, dateStr)

driver.get(LOGIN_URL)
load_cookie(driver)

if Authenthicate(pageTravList):
    getData(pageTravList)
    print(pageTravList)
    save_cookie(driver)
else:
    print("log in error")
    print(pageTravList)
#df_ori=pd.read_csv(dateStr+'.csv', keep_default_na=False)

driver.close()
sys.exit(0)