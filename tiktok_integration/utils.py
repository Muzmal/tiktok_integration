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
from frappe.utils import cstr, flt, cint, get_files_path
from PIL import Image
import requests
from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData
import base64



@frappe.whitelist( )
def receive_code_from_tiktok():
    app_details = frappe.get_doc('Tiktok with ERPnext') 
    if( app_details.is_sandbox == True ):
        url = 'https://auth-sandbox.tiktok-shops.com'
    else:
        url = 'https://auth.tiktok-shops.com'
    code = frappe.request.args['code']
     
    app_secret = app_details.get_password('app_secret')
    params = {'app_key' :app_details.app_key,'app_secret' : app_secret ,"auth_code":code , "grant_type":"authorized_code" }
     
    url = url+'/api/v2/token/get'
     
    response = requests.get(url,params)
     
    data = response.json()
    frappe.msgprint( data['message'] )

    if( data['message']=='success' ):
        doc = frappe.get_doc('Tiktok with ERPnext')
        doc.access_token=data['data']['access_token']
        doc.refresh_token=data['data']['refresh_token']
        doc.save(
             ignore_permissions=True, # ignore write permissions during insert
             ignore_version=True # do not create a version record
        )

        frappe.db.commit()
        
        url = frappe.utils.get_url()+app_details.get_url()
        
        webbrowser.open( url,new=0 )
    else :
        print(f"\n\n not working like this ")

    return  


@frappe.whitelist(allow_guest=True)
def webhook_tiktok( **kwargs ):
    signature = frappe.request.headers.get("Authorization")
    save_order = saveTiktokData()
    app_details = frappe.get_doc('Tiktok with ERPnext') 
    app_secret = app_details.get_password('app_secret')
    response=frappe._dict(kwargs)
    get_data = frappe.request.get_data()
    string_to_sign = app_details.app_key + str(get_data,'utf-8')
    signature1=hmac.new(bytes(app_secret, 'UTF-8'), string_to_sign.encode('UTF-8'), hashlib.sha256).hexdigest()
    print(  f" get_data: {get_data}  signature1 : {signature1}, signature : {signature}"  )
    veification =  hmac.compare_digest( signature1,signature ) 
    if( veification ):
        data=response['data']
        if( response['type']==1 ):
            prev_order = save_order._checkIfOrderExists( data['order_id'],data['order_status'] )
            if( prev_order == False ):
                order_list=[]
                order_list.append(data['order_id'])
                save_order._fetchOrderDetails(order_list,"addNew")
        print(f"\n\n\n webhook is called again  please verify {data} \n\n\n")
    else:
        print(f"\n\n\n webhook is called with wrong signature \n\n\n")
    return
