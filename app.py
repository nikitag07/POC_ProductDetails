#!/usr/bin/env python
# coding: utf-8

# In[16]:


#Import classes
from flask import Flask, render_template, json, request ,jsonify, redirect     # import flask
from bs4 import BeautifulSoup
from flask import *
import requests
from lxml import etree
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
import time 
# import libraties
import pandas as pd
import numpy as np
# hide warnings
import warnings
warnings.filterwarnings('ignore')


# In[22]:


#Intitate Flask and handle all request and response
app = Flask(__name__)             # create an app instance

# @app.route("/<name>")              # at the end point /<name>
# def hello_name(name):              # call method hello_name
#     return "Hello "+ name          # which returns "hello + name 
# which returns "hello world"

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/search',methods=['POST'])
def search():
    # create user code will be here !!
     # read the posted values from the UI
    print('inside search')
    textvalue = request.json['input']
    print(textvalue)
    output_df = callengine(textvalue)
    output_df.to_csv('product_aggregation.csv', index=False)
   
    return jsonify({"response" : textvalue})


@app.route('/results',methods=("GET", "POST"))  
def showresult():  
    input_data = pd.read_csv('product_aggregation.csv', encoding='latin-1')
    input_data['product_price'] = input_data['product_price'].str.replace(r'AED', '')
    input_data['product_price'] = input_data['product_price'].str.replace(r'Â', '')
    input_data['product_price'] = input_data['product_price'].str.replace('(In Deal)', '')
    input_data['product_price'] = input_data['product_price'].str.replace('\nInclusive of VAT', '')
    input_data['product_price'] = input_data['product_price'].str.replace(',', '')
    input_data = input_data.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    input_data["product_price"] = pd.to_numeric(input_data["product_price"])
    input_data = input_data.sort_values(by=['product_price'],ascending=True)
    return render_template('simple.html',tables=[input_data.to_html()],
    titles = ['na', 'Product Results'])
    
@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response    
    
if __name__ == "__main__":        #
    app.run()
    # run the flask app


# In[17]:


#Method to scrap data from amazon through Beautiful Soup
def main_amazon(URL,product_df): 
    
    print('inside amazon')
    # specifying user agent, You can use other user agents 
    # available on the internet 
    HEADERS = ({'User-Agent': 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36', 
                                'Accept-Language': 'en-US, en;q=0.5'}) 
    
   # driver = webdriver.Chrome('Path in your computer where you have installed chromedriver')
  
    # Making the HTTP Request 
    webpage = requests.get(URL, headers=HEADERS) 
  
    # Creating the Soup Object containing all data 
    soup = BeautifulSoup(webpage.content, "lxml") 
  
    # retreiving product title 
    try: 
        # Outer Tag Object 
        title = soup.find("span",  
                          attrs={"id": 'productTitle'}) 
  
        # Inner NavigableString Object 
        title_value = title.string 
        # Title as a string value 
        title_string = title_value.strip().replace(',', '') 
  
    except AttributeError: 
        title_string = "NA"
    print("product Title = ", title_string) 
  
    # saving the title in the file 
    #File.write(f"{title_string},") 
  
    # retreiving price 
    try: 
        price = soup.find( 
            "span", attrs={'id': 'priceblock_ourprice'}).string.strip().replace(',', '') 
        # we are omitting unnecessary spaces 
        # and commas form our string 
    except AttributeError: 
        try:
            price = soup.find( 
                "span", attrs={'id': 'priceblock_dealprice'}).string.strip().replace(',', '') 
            price = price
            
        except AttributeError:
            price = "NA"
        
    print("Products price = ", price) 
  
    # retreiving product rating 
    try: 
        rating = soup.find("i", attrs={ 
                           'class': 'a-icon a-icon-star a-star-4-5'}).string.strip().replace(',', '') 
  
    except AttributeError: 
  
        try: 
            rating = soup.find( 
                "span", attrs={'class': 'a-icon-alt'}).string.strip().replace(',', '') 
        except: 
            rating = "NA"
    rating = rating.replace('out of 5 stars','')
    print("Overall rating = ", rating) 
  
    #File.write(f"{rating},") 
  
    try: 
        review_count = soup.find( 
            "span", attrs={'id': 'acrCustomerReviewText'}).string.strip().replace(',', '') 
  
    except AttributeError: 
        review_count = "NA"
    print("Total reviews = ", review_count) 
    #File.write(f"{review_count},") 
    
    # print availiblility status 
    try: 
        available = soup.find("div", attrs={'id': 'availability'}) 
        available = available.find("span").string.strip().replace(',', '') 
  
    except AttributeError: 
        available = "NA"
    print("Availability = ", available) 
      
    new_row = {'vendor':'amazon', 'product_title':title_string,
               'product_price':price,'Rating':rating,'Reviews':review_count,'Availability':available}
   
    return product_df.append(new_row, ignore_index=True)


# In[18]:


#Method to scrap data from noon, using selenium as reviews and ratings are not present as static and in form of hyperlink
def main_noon1(URL,driverpath,product_df):
    # openning our output file in append mode 
    #File = open("out.csv", "a") 
  
    # specifying user agent, You can use other user agents 
    # available on the internet 
    HEADERS = ({'User-Agent': 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36', 
                                'Accept-Language': 'en-US, en;q=0.5'}) 
    # Making the HTTP Request 
    webpage = requests.get(URL, headers=HEADERS) 
    # Creating the Soup Object containing all data 
    soup = BeautifulSoup(webpage.content, "lxml") 
    driver = webdriver.Chrome(driverpath)
   
    driver.get(URL)
    time.sleep(5)
    #retreiving product title 
    try: 
        title = driver.find_elements_by_xpath('.//h1[@class="sc-1vbk2g0-8 cfCaBu"]')[0].text
  
        #print(title)
        # Inner NavigableString Object 
        title_value = title 
  
        # Title as a string value 
        title_string = title_value.strip().replace(',', '') 
  
    except AttributeError: 
        title_string = "NA"
    print("product Title = ", title_string) 

  
    #retreiving price 
    try: 

        price = driver.find_elements_by_xpath('.//div[@class="priceNow"]')[0].text
        price = price.replace('(Inclusive of VAT)','')
        price = price. rstrip('\n')
        #price = price.text
    except AttributeError: 
        price = "NA"
    print("Products price = ", price) 
  

    try: 
        available = driver.find_elements_by_xpath('.//div[@class="sc-1xw7r3i-0 grpnyI"]')
        #available = available.find("span").string.strip().replace(',', '') 
        if (available.length==0):
            available_string = 'In Stock.'
        else:
            available_string = 'Sorry! This product is not available.'
    except AttributeError: 
        available_string = 'In Stock.'
    print("Availability = ", available_string) 

    
    #retreiving product rating
    try:
        element = driver.find_elements_by_xpath('.//button[@id="Reviews"]')
        element[0].click()
    except ElementNotVisibleException:
        pass
    try:
        rating = driver.find_elements_by_xpath('.//div[@class="overallRating"]')[0].text
    except AttributeError: 
        rating = "NA"
    print("Overall rating = ", rating) 
    
    #retreiving review count
    try: 
        review_count = driver.find_elements_by_xpath('.//div[@class="basedOn"]')[0].text
    except AttributeError: 
        review_count = "NA"
    review_count = review_count.replace('Based on ','')#Based on 
    print("Total reviews = ", review_count) 
    
    # closing the file and driver
    driver.close()
    new_row = {'vendor':'noon', 'product_title':title_string,
               'product_price':price,'Rating':rating,'Reviews':review_count,'Availability':available_string}
   
    return product_df.append(new_row, ignore_index=True)


# In[20]:


#Method to scrap data from noon using beatuiful soup
def main_sharafdg(URL,product_df): 
    
    # specifying user agent, You can use other user agents 
    # available on the internet 
    HEADERS = ({'User-Agent': 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36', 
                                'Accept-Language': 'en-US, en;q=0.5'}) 
    
   # driver = webdriver.Chrome('Path in your computer where you have installed chromedriver')
  
    # Making the HTTP Request 
    webpage = requests.get(URL, headers=HEADERS) 
  
    # Creating the Soup Object containing all data 
    soup = BeautifulSoup(webpage.content, "lxml") 
  
    # retreiving product title 
    try: 
        # Outer Tag Object 
        title = soup.find("h1",  
                          attrs={"class": 'product_title entry-title'}) 
  
        # Inner NavigableString Object 
        title_value = title.string 
  
        # Title as a string value 
        title_string = title_value.strip().replace(',', '') 
  
    except AttributeError: 
        title_string = "NA"
    print("product Title = ", title_string) 
  
    # saving the title in the file 
    #File.write(f"{title_string},") 
  
    # retreiving price 
    try: 
        currency = soup.find( 
            "span", attrs={'class': 'currency'}).string
        price = soup.find( 
            "span", attrs={'class': 'total--sale-price'}).string
        # we are omitting unnecessary spaces 
        # and commas form our string 
    except AttributeError: 
        price = "NA"
    print("Products price = ", currency+' '+price) 
  
    # saving 
    #File.write(f"{price},") 
  
    # retreiving product rating 
    try: 
        rating = soup.find("span", attrs={ 
                           'class': 'product-rating-count'}).string.strip().replace('(', '') .replace(')','')
  
    except AttributeError: 
        rating = "NA"
    rating = rating.replace('out of 5 stars','')
    print("Overall rating = ", rating) 
  
    #File.write(f"{rating},") 
  
    try: 
        review_count = soup.find( 
            "span", attrs={'itemprop': 'reviewCount'}).string.strip().replace(',', '') 
        review_count = review_count+" ratings"
    except AttributeError: 
        review_count = "NA"
    print("Total reviews = ", review_count) 
    #File.write(f"{review_count},") 
    
    # print availiblility status 
    try: 
        available = soup.find("p", attrs={'id': 'out-of-stock-box'}) 
        available = available.string
  
    except AttributeError: 
        available = "In Stock"
    print("Availability = ", available) 
      
    new_row = {'vendor':'sharafdg', 'product_title':title_string,
               'product_price':currency+' '+price,'Rating':rating,'Reviews':review_count,'Availability':available}
   
    return product_df.append(new_row, ignore_index=True)


# In[ ]:


# Testing
#output_df = callengine('iPhone 11 Pro Max 256 GB')


# In[ ]:


# input_data = pd.read_csv('inputdata.csv', encoding='latin-1')
# inputvalue = 'iPhone 11 Pro Max 256 GBB'
# input_data.loc[input_data['keyword'] == inputvalue]
# filter_data = input_data.loc[input_data['keyword'] == inputvalue]
# filter_data.head()
# if(filter_data.empty):


# In[ ]:


# input_data = pd.read_csv('product_aggregation.csv', encoding='latin-1')
# input_data['product_price'] = input_data['product_price'].str.replace(r'AED', '')
# input_data['product_price'] = input_data['product_price'].str.replace(r'Â', '')
# input_data['product_price'] = input_data['product_price'].str.replace('(In Deal)', '')
# input_data['product_price'] = input_data['product_price'].str.replace('\nInclusive of VAT', '')
# input_data['product_price'] = input_data['product_price'].str.replace(',', '')
# input_data = input_data.applymap(lambda x: x.strip() if isinstance(x, str) else x)
# #print (df)
# input_data["product_price"] = pd.to_numeric(input_data["product_price"])
# input_data = input_data.sort_values(by=['product_price'],ascending=True)
# input_data.head()


# In[21]:


#Engine to scrap all the data and insert into dataframe
def callengine(inputvalue):
    # Reading links_data file
    print(inputvalue)
    input_data = pd.read_csv('inputdata.csv', encoding='latin-1')
    #inputvalue = 'Macbook Pro 13inch'
    filter_data = input_data.loc[input_data['keyword'] == inputvalue]
    #print(filter_data)
    if filter_data.empty:
        return filter_data
    else:
        cols = ['vendor','product_title','product_price','Rating','Reviews','Availability']
        product_df = pd.DataFrame(columns = cols)
        print('**************Amazon*****************')
        product_df = main_amazon(filter_data['amazon'].item(),product_df)
        print('**************Noon*****************')
        driver_path = input_data.loc[input_data['keyword'] == 'chromedriver']
        
        product_df = main_noon1(filter_data['noon'].item(),driver_path['amazon'].item(),product_df)
        print('**************SharafDG*************')
        product_df = main_sharafdg(filter_data['sharafdg'].item(),product_df)
        return product_df

