import frappe
from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData
import json
import requests
import calendar;
from datetime import datetime
import time
try:
    import urlparse
    from urllib import urlencode
except: # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

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
    print(url)
    headers = {
    'Content-Type': 'application/json'
    }		
    try:
        res = requests.get(url, headers=headers)
        if( res.json() ):
            data = res.json()
            half = len(data['data']['category_list']) / 2
            #print("half1111 "+ data['data']['category_list'][985]  )
            
            if (half % 2 != 0):
                half1 = len(data['data']['category_list'])/2
                rounded_down = int(half1 // 1)
                
                half2 = len(data['data']['category_list'])/2
                rounded_up = int(half2 // 1 + 1)

                app_details.main_category=json.dumps(data['data']['category_list'][:rounded_up])
                app_details.main_category_2=json.dumps(data['data']['category_list'][rounded_down:])
            else :
                app_details.main_category=json.dumps(data['data']['category_list'][:half])
                app_details.main_category_2=json.dumps(data['data']['category_list'][half:])
            
            
            app_details.save()
    except:
        print("exception")
    
    # print( app_details.main_category )
    # print( data['data']['category_list'][:rounded_up] )
    # print( app_details.main_category_2 )

    return "data['data']['category_list']"


@frappe.whitelist( )
def send_categories(  ):
    app_details = frappe.get_doc('Tiktok with ERPnext') 
    dictA = json.loads(app_details.main_category)
    dictB = json.loads(app_details.main_category_2)
    dictA.extend(dictB)


    val = json.dumps(dictA)
    return val

@frappe.whitelist( )
def updateTiktokProduct( web_item ):
    web_item = str(web_item)
    marketplace_id=False
    # item=frappe.get_doc("Website Item",web_item)
    tiktok_item=None
    # if( item is not None ):
    tiktok_item=frappe.get_doc("Tiktok Item",web_item)
    if( tiktok_item is not None ):
        marketplace_id=tiktok_item.marketplace_id

    if( marketplace_id ):
        val = updateTiktokShopProduct( tiktok_item,marketplace_id )
    return val

@frappe.whitelist( )
def updateTiktokShopProduct( item,product_id ):
    path='/api/products'
    app_details = frappe.get_doc('Tiktok with ERPnext')
    access_token = app_details.get_password('access_token')
    app_secret = app_details.get_password('app_secret')
    gmt = time.gmtime()
    timestamp = calendar.timegm(gmt)    
    query = {
        "app_key":app_details.app_key,
        'access_token':access_token,
        'timestamp':timestamp,
        "product_id":product_id,
        "product_name":item.tiktok_shop_item_name,
        "category_id":"601476",
        "package_weight":item.weight_kg,
        "description":item.product_description,
    }
    query_var=urlencode(query)
    params_for_sign = query
    del params_for_sign['access_token']
    ##################################
    tiktok=saveTiktokData()
    signature = tiktok._getSignature(path,params_for_sign,app_secret)


    if( app_details.is_sandbox == True ):
        url = 'https://open-api-sandbox.tiktokglobalshop.com'
    else:
        url = 'https://open-api.tiktokglobalshop.com/'


    payload = json.dumps({
    "skus": json.loads( item.skus_to_update_api_product),
    "images": json.loads(item.images_ids_to_update)
    })
   
    

    headers = {
    'Content-Type': 'application/json'
    }

    
    url = url+path+"?"+query_var+"&sign="+signature
    
    response = requests.request("PUT", url, headers=headers, data=payload)
    data = response.json()
    if( data['code']==0 ):
        frappe.msgprint("Product is updated successfully")
    else:
        frappe.msgprint("Something went wrong while updating product")
    
    return payload