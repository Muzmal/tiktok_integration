import frappe
from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData
import json
import requests
import calendar;
from datetime import datetime
import time

@frappe.whitelist( )
def fetch_categories(  ):
    
    path='/api/products/categories'
    app_details = frappe.get_doc('Tiktok with ERPnext') 
    access_token = app_details.get_password('access_token')
    app_secret = app_details.get_password('app_secret')
    gmt = time.gmtime()
    timestamp = calendar.timegm(gmt)
    
    
    query = {
            "app_key":app_details.app_key,
            'access_token':access_token,
            'timestamp':timestamp,
        }
    
    if( app_details.is_sandbox == True ):
        url = 'https://open-api-sandbox.tiktokglobalshop.com'
    else:
        url = 'https://open-api.tiktokglobalshop.com/'
    params_for_sign = query
    del params_for_sign['access_token']

    tiktok=saveTiktokData()
    signature = tiktok._getSignature(path,params_for_sign,app_secret)
    
    url = url+path+"?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&sign="+str(signature)+"&timestamp="+str(timestamp)
    payload = json.dumps({
    })
    headers = {
    'Content-Type': 'application/json'
    }		
    try:
        res = requests.get(url, headers=headers)
        if( res.json() ):
            data = res.json()
            return data['data']['category_list']
    except:
        print("exception")
        
    return "data['data']['category_list']"