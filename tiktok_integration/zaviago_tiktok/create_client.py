# Copyright (c) 2023, Zaviago and contributors
# For license information, please see license.txt

import base64
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import frappe
import requests
from frappe import _
from frappe.utils import cint, cstr, get_datetime
from pytz import timezone
import random
import webbrowser
import json

class CreateTiktokClient:

	def start_connecting( self, app_key , app_secret, is_sandbox ):
		return self.createAuthRequest(app_key,app_secret,is_sandbox)
		
	def createAuthRequest( self, app_key , app_secret, is_sandbox ):
		url='empty'
		if( is_sandbox == True ):
			url = 'https://auth-sandbox.tiktok-shops.com'
		else:
			url = 'https://auth.tiktok-shops.com'
		state = random.randint(0,10000)
		params = {'app_key' : app_key,'state' : state }
		qstr = urlencode(params)
		url = url+'/?'+qstr
		return url
	
	def refreshToken( self ):
			app_details = frappe.get_doc('Tiktok with ERPnext') 
			url='empty'
			if( app_details.is_sandbox == True ):
				url = 'https://auth-sandbox.tiktok-shops.com'
			else:
				url = 'https://auth.tiktok-shops.com'
			state = random.randint(0,10000)
			url = url+'/api/v2/token/refresh'
			url = url+"?app_key="+str(app_details.app_key)+"&app_secret="+app_details.get_password('app_secret')+"&refresh_token="+app_details.refresh_token+"&grant_type=refresh_token"
			headers = {
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url, headers=headers )
			data = response.json()
			if( data['message']=='success' ):
				frappe.db.set_value('Tiktok with ERPnext','','access_token',data['data']['access_token'])
				frappe.db.set_value('Tiktok with ERPnext','','refresh_token',data['data']['refresh_token'])
				frappe.db.commit()
				
				url = frappe.utils.get_url()+app_details.get_url()
			else :
				print(f"\n\n not working like this ")
			
	
	def get_token_from_code():
		frappe.msgprint(frappe.request.args)

@frappe.whitelist( )
def redirect_to_auth(  ):
	app_details = frappe.get_doc('Tiktok with ERPnext') 
	if( app_details.app_key!='' and app_details.app_secret != '' and app_details.enable_tiktok ):
			connect = CreateTiktokClient()	
			url = connect.start_connecting ( app_details.app_key,app_details.app_secret,app_details.is_sandbox )
			if( url ):
				print (f"Redirecting to auth from function {url}")
				response_ = {'url':url}
				return response_
				exit() 
				
	return   
	