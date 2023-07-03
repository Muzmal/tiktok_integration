from wsgiref.util import request_uri
import frappe
from urllib.parse import urlencode
import webbrowser
import requests
import json
import unicodedata
import calendar;
import time;
import hashlib
import hmac
import binascii

from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData

@frappe.whitelist( )
def receive_code_from_tiktok():
    app_details = frappe.get_doc('Tiktok with ERPnext') 
    if( app_details.is_sandbox == True ):
        url = 'https://auth-sandbox.tiktok-shops.com'
    else:
        url = 'https://auth.tiktok-shops.com'
    code = frappe.request.args['code']
    print(f"\n\n{code}")
    app_secret = app_details.get_password('app_secret')
    params = {'app_key' :app_details.app_key,'app_secret' : app_secret ,"auth_code":code , "grant_type":"authorized_code" }
     
    url = url+'/api/v2/token/get'
     
    response = requests.get(url,params)
     
    data = response.json()
    frappe.msgprint( data['message'] )

    if( data['message']=='success' ):
        frappe.db.set_value('Tiktok with ERPnext','','access_token',data['data']['access_token'])
        frappe.db.set_value('Tiktok with ERPnext','','refresh_token',data['data']['refresh_token'])
        frappe.db.commit()
        
        url = frappe.utils.get_url()+app_details.get_url()
        print(f"\n\n url is {url} ")
        webbrowser.open( url,new=0 )
    else :
        print(f"\n\n not working like this ")

    return  



@frappe.whitelist(allow_guest=True)
def webhook_tiktok(  **kwargs ):

    app_details = frappe.get_doc('Tiktok with ERPnext') 
    # data=frappe.request['post']
    response=frappe._dict(kwargs)

    data=response['data']
    if( response['type']==1 ):
        save_order = saveTiktokData()
        order_list=[]
        order_list.append(data['order_id'])
        save_order._fetchOrderDetails(order_list)
     
    print(f"\n\n\n webhook is called again  please verify {data} \n\n\n")
     

    return
