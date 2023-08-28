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
import json
from frappe.utils import today
import calendar;
import time;
import hashlib
import hmac
import binascii
from datetime import datetime

class saveTiktokData:
	orderData=[]
	def _checkIfOrderExists(self , tiktok_order,order_status ):
		prev_order = frappe.db.exists({"doctype": "Sales Order", "tiktok_order_id": tiktok_order})
		
		if( prev_order ):
			doc = frappe.get_doc("Sales Order", {"tiktok_order_id": tiktok_order})
			order=[]
			order.append(tiktok_order)
			updated_order = self._fetchOrderDetails( order,"Update" )
			print(  f"\n\n\n\n\n  _checkIfOrderExists order is {updated_order}" )
			self._save_tiktok_order(updated_order,"Update",doc)
			# doc.tiktok_order_status =  order_status 
			return True
		else:
			return False
	

	def _fetchOrderDetails(self,orderIDs,isNew):
		############################### get order details
		print("\n\n\n fetchting order details \n\n\n")
		path='/api/orders/detail/query'
		app_details = frappe.get_doc('Tiktok with ERPnext')
		access_token = app_details.get_password('access_token')
		app_secret = app_details.get_password('app_secret')
		gmt = time.gmtime()
		timestamp = calendar.timegm(gmt)    
		# string_to_sign
		query = {
			"app_key":app_details.app_key,
			'access_token':access_token,
			'limit':20,
			'timestamp':timestamp,
		}
		params_for_sign = query
		del params_for_sign['access_token']
	
		##################################
		signature = self._getSignature(path,params_for_sign,app_secret)
		##################################
		if( app_details.is_sandbox ):
			uri = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			uri = 'https://open-api.tiktokglobalshop.com'
		url = uri+path+"?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&limit=20&sign="+str(signature)+"&timestamp="+str(timestamp)

		payload = json.dumps({
		#"order_id_list": ['577463955647466245']
		"order_id_list": orderIDs
		})
		headers = {
		'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		#################################
		data = response.json()
		print( f"\n\n showing single order \n\n" ) 
		if( data['code']==0 ):
			if( isNew=='Update' ):
				print(f"\n\n\n\n order to update in fetch order is {data['data']['order_list']}  \n\n\n\n")
				return data['data']['order_list']
			else:
				print(f"\n\n\n\n order to add new is {data['data']['order_list']}  \n\n\n\n")
				self._save_tiktok_order(data['data']['order_list'],"New",'')
		return 
	

	def fetchProduct( self,product_id,return_image ):
		
		imgUrl=False
		path='/api/products/details'
		app_details = frappe.get_doc('Tiktok with ERPnext') 
		access_token = app_details.get_password('access_token')
		app_secret = app_details.get_password('app_secret')
		gmt = time.gmtime()
		timestamp = calendar.timegm(gmt)   
		if( app_details.is_sandbox == True ):
			url = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			url = 'https://open-api.tiktokglobalshop.com/'
		query = {
				"app_key":app_details.app_key,
				'access_token':access_token,
				'timestamp':timestamp,
				'product_id':str(product_id)
			}
		
		params_for_sign = query
		del params_for_sign['access_token']
		tiktok = saveTiktokData()
		signature = tiktok._getSignature(path,params_for_sign,app_secret)
		url = url+path+"?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&sign="+str(signature)+"&timestamp="+str(timestamp)+"&product_id="+str(product_id)
		payload = json.dumps({
		#"order_id_list": ['577463955647466245']
		"product_id": '1729622829106760283'
		})
		headers = {
		'Content-Type': 'application/json'
		}
		res = requests.get(url, headers=headers, data=payload )
		data = res.json()
		if( return_image==True ):
			if( data['code'] == 0 ):
				img = data['data']
				img = img['images']
				for i in img:
					imgUrl = i['thumb_url_list'][0] 
					break
			return_value= imgUrl
		else:
			return_value = data['data']
		self.orderData=data['data']
		print(f" return value is {return_value}")
		return return_value
		
		

	def _save_sales_invoice(self,o):
		
		new_order = frappe.new_doc('Sales Invoice')
		
		# new_order.price_list_currency=o['payment_info']['currency']
		date = o['create_time']
		date = int(date)/1000
		date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d') 
		new_order.transaction_date=date
		new_order.delivery_date=date
		new_order.due_date=today()
		new_order.customer=o['recipient_address']['name']
		# new_order.tiktok_order_id=o['order_id']
		# new_order.marketplace_name="Tiktok"
		# new_order.marketplace_order_number=o['order_id']
		# new_order.marketplace="Tiktok"
		for product in o['item_list']:
			if( product['seller_sku'] =='' ):
				product['seller_sku']="no-sku-"+str(product['product_id'])
			# item_code = product['seller_sku']
			# Item = frappe.db.exists("Item", str(item_code))
			# if( Item == None ):
			# 	self._create_product(product['product_name'],product['seller_sku'],"By-product","no")
			# 	p_img = self.fetchProduct( product['product_id'],return_image=True )
			# 	self.saveTiktokProductWebhook(self.orderData)
			# 	if( p_img ):
			# 		print(f" Got product image { p_img }")
			# 		self.addImageToItem(p_img,product['seller_sku'])
				# tiktok_doc = TiktokwithERPnext()
				# ifExist=self.checkIfDocExists( product['product_id'] )
				# if( ifExist == None ):	
				# 	tiktok_doc.saveTiktokProduct( product )
			new_order.append("items",{
				"item_code": product['seller_sku'],
				"item_name": product['product_name'],
				"uom": "Kg",
				"qty": product['quantity'],
				"price_list_rate": product['sku_original_price'],
				"rate": product['sku_original_price'],
				"amount": product['sku_sale_price'],
				"stock_uom_rate": product['sku_original_price'],
				"net_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
				"net_amount": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
				"billed_amt": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
				"valuation_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
				})	
		p_info=payment_info=o['payment_info']
		if( 'shipping_fee' in p_info ):
				
				# shipping = frappe.db.exists("Item", 'item_shipping_cost')
				# if( shipping == None ):
				# 	self._create_product(product['product_name'],product['seller_sku'],"By-product","yes")
				shipping_provider="Tiktok Shipping"
				payment_info=o['payment_info']
				shipping_fee=payment_info['original_shipping_fee']
				shipping_fee=shipping_fee-payment_info['shipping_fee_platform_discount']
				shipping_fee=shipping_fee-payment_info['shipping_fee_seller_discount']

				new_order.append("items",{
				"item_code": 'item_shipping_cost',
				"item_name": shipping_provider,
				"uom": "Kg",
				"qty": "1",
				"price_list_rate": shipping_fee,
				"rate": shipping_fee,
				"amount": shipping_fee,
				"stock_uom_rate": shipping_fee,
				"net_rate": shipping_fee,
				"net_amount": shipping_fee,
				"billed_amt": shipping_fee,
				"valuation_rate": shipping_fee,
				})	
		response = new_order.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		new_order.submit()
		frappe.db.commit()
		return


	def _save_tiktok_order( self,orders,existingOrder,savedOrder ):
		print(f"\n\n\n\n order to update is {orders}  \n\n\n\n")
		for o in orders: 
			if( existingOrder == 'New' ):
				prev_order = frappe.db.exists({"doctype": "Sales Order", "tiktok_order_id": o['order_id']})
				if( prev_order ):
					print(f"\n\n Order is already saved {prev_order}: {o['order_id']} \n\n")
					continue
				else:
					new_order = frappe.new_doc('Sales Order')
					new_order.price_list_currency=o['payment_info']['currency']
					date = o['create_time']
					date = int(date)/1000
					date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d') 
					new_order.transaction_date=date
					new_order.delivery_date=date
					new_order.tiktok_order_id=o['order_id']
					# new_order.marketplace_name="Tiktok"
					new_order.marketplace_order_number=o['order_id']
					new_order.marketplace="Tiktok"
					for product in o['item_list']:
						if( product['seller_sku'] =='' ):
							product['seller_sku']="no-sku-"+str(product['product_id'])
						item_code = product['seller_sku']
						Item = frappe.db.exists("Item", str(item_code))
						if( Item == None ):
							self._create_product(product['product_name'],product['seller_sku'],"By-product","no")
							p_img = self.fetchProduct( product['product_id'],return_image=True )
							self.saveTiktokProductWebhook(self.orderData)
							if( p_img ):
								print(f" Got product image { p_img }")
								self.addImageToItem(p_img,product['seller_sku'])
							# tiktok_doc = TiktokwithERPnext()
							# ifExist=self.checkIfDocExists( product['product_id'] )
							# if( ifExist == None ):	
							# 	tiktok_doc.saveTiktokProduct( product )
						new_order.append("items",{
							"item_code": product['seller_sku'],
							"item_name": product['product_name'],
							"uom": "Kg",
							"qty": product['quantity'],
							"price_list_rate": product['sku_original_price'],
							"rate": product['sku_original_price'],
							"amount": product['sku_sale_price'],
							"stock_uom_rate": product['sku_original_price'],
							"net_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
							"net_amount": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
							"billed_amt": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
							"valuation_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
							})	
					p_info=payment_info=o['payment_info']
					if( 'shipping_fee' in p_info ):
							
							shipping = frappe.db.exists("Item", 'item_shipping_cost')
							if( shipping == None ):
								self._create_product(product['product_name'],product['seller_sku'],"By-product","yes")
							shipping_provider="Tiktok Shipping"
							payment_info=o['payment_info']
							shipping_fee=payment_info['original_shipping_fee']
							shipping_fee=shipping_fee-payment_info['shipping_fee_platform_discount']
							shipping_fee=shipping_fee-payment_info['shipping_fee_seller_discount']

							new_order.append("items",{
							"item_code": 'item_shipping_cost',
							"item_name": shipping_provider,
							"uom": "Kg",
							"qty": "1",
							"price_list_rate": shipping_fee,
							"rate": shipping_fee,
							"amount": shipping_fee,
							"stock_uom_rate": shipping_fee,
							"net_rate": shipping_fee,
							"net_amount": shipping_fee,
							"billed_amt": shipping_fee,
							"valuation_rate": shipping_fee,
							})	

					
			else:
				new_order = frappe.get_doc("Sales Order", {"tiktok_order_id": o['order_id']})
				# new_order.tiktok_order_status = self.fetchStatusFromCode( o['order_status'] )
				# new_order.save()
				# return

			new_order.title=o['recipient_address']['name']			
			customer_flag = frappe.db.exists("Customer", o['recipient_address']['name'] )
			if( customer_flag == None ):
				self._create_customer( o['recipient_address'],o['recipient_address']['name'] )
			
			new_order.customer=o['recipient_address']['name']
			new_order.order_type="Sales"
			
			
			new_order.tiktok_order_status = self.fetchStatusFromCode( o['order_status'] )
			
			 
			if( existingOrder =="Update" ):
				new_order.flags.ignore_mandatory = True
				new_order.save(
					ignore_permissions=True, # ignore write permissions during insert
				)
				new_order.submit()
				return
			else :
				response = new_order.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
				new_order.submit()
				self._save_sales_invoice(o)
			

			
			frappe.msgprint("Created order")
		return
	
	def _create_customer(self,order_address,customer_name):
		print( f"  \n \n \n \n  Creating customer  \n \n \n \n ")
		# customer_group_name
		# customer_group  = frappe.db.exists({"doctype": "Customer Group", "customer_group_name": "Tiktok"})
		customer_group = frappe.db.exists("Customer Group", "Tiktok")
		if( customer_group == None ):
			print( f"  \n \n \n \n  Creating customer group \n \n \n \n ")
			new_customer_group = frappe.new_doc('Customer Group')
			new_customer_group.customer_group_name="Tiktok"
			new_customer_group.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
				
		# territory  = frappe.db.exists({"doctype": "Territory", "territory_name": "Thailand"})
		territory = frappe.db.exists("Territory", "Thailand")
		if( territory == None ):
			print( f"  \n \n \n \n  Creating customer territory \n \n \n \n ")
			new_territory = frappe.new_doc('Territory')
			
			new_territory.territory_name="Thailand"
			new_territory.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)

		new_customer = frappe.new_doc('Customer')
		new_customer.customer_name=customer_name
		new_customer.customer_group="Tiktok"
		new_customer.territory="Thailand"
		response = new_customer.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		print("  \n \n \n \n  Created customer")
		

		country = zav_country_map.get(order_address["region_code"])
		address_type = "Billing"
		also_shipping=False
		frappe.get_doc(
		{
			"address_line1": order_address["full_address"] or "Not provided",
			"address_line2": '',
			"address_type": address_type,
			"city": order_address["city"],
			"country": country,
			"county": order_address["district"],
			"doctype": "Address",
			"phone": order_address["phone"],
			"links": [{"link_doctype": "Customer", "link_name": customer_name}],
			"is_primary_address": int(address_type == "Billing"),
			"is_shipping_address": int(also_shipping or address_type == "Shipping"),
		}
		).insert(
			ignore_mandatory=True,
			ignore_permissions=True, # ignore write permissions during insert
			ignore_links=True, )
			
		

	def _create_product(self,item_name,item_code,item_group,is_shipping):
		item_group="Tiktok"
		if( is_shipping=='yes' ):
			item_name='shipping'
			item_code='item_shipping_cost'
		Item = frappe.new_doc('Item')
		Item.item_name=item_name
		Item.item_code=item_code
		item_group = frappe.db.exists("Item Group", item_group )
		if( item_group == None ):
			print( f"  \n \n \n \n  Creating item group   \n \n \n \n ")
			new_item_group = frappe.new_doc('Item Group')
			new_item_group.item_group_name="Tiktok"
			new_item_group.parent_item_group="All Item Groups"
			new_item_group.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)

		Item.item_group="Tiktok"
		
		
		response = Item.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		frappe.db.commit()
		frappe.msgprint("Created Item")
		print("Created Item is")
		print(f"\n\n {Item} ")
		return


	def _getSignature( self,path,params,app_secret ):
		signature = ''
		string_to_sign=''
		params_for_sign = params
		myKeys = list(params_for_sign.keys())
		myKeys.sort()
		sorted_params_for_sign = {i: params_for_sign[i] for i in myKeys}
		for k,v in sorted_params_for_sign.items():
			string_to_sign=string_to_sign+str(k)+str(v)
		string_to_sign = path+string_to_sign
		string_to_sign = app_secret+string_to_sign+app_secret
		signature=hmac.new(bytes(app_secret, 'UTF-8'), string_to_sign.encode(), hashlib.sha256).hexdigest()
		return signature
	

	def fetchStatusFromCode(self,statusCode):
		if( statusCode==111 ):
			return 'AWAITING_SHIPMENT'
		elif( statusCode==112 ):
			return 'AWAITING_COLLECTION'
		elif( statusCode==114 ):
			return 'Partial'
		elif( statusCode==121 ):
			return 'In-Transit'
		elif( statusCode==122 ):
			return 'Delivered'
		elif( statusCode==130 ):
			return 'Completed'
		elif( statusCode==140 ):
			return 'Cancelled'
		else:
			return 'UNPAID'
		
	def addImageToItem(self,image_url,item_title):

		new_file = frappe.new_doc("File")
		new_file.file_name=str(item_title)+"_photo.jpeg"

		new_file.attached_to_doctype='Item'
		new_file.attached_to_name=str(item_title)

		new_file.file_url=image_url
		response = new_file.insert(
				ignore_mandatory=True,
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, )
		frappe.db.commit()
		return

	def saveTiktokProductWebhook( self,tiktokProduct ):
		if( self.checkIfDocExistsWebhook( tiktokProduct['product_id'] )==False ):
			return
		#start adding product in tiktok doctype
		new_product = frappe.new_doc('Tiktok Products')
		k = 0
		is_variable=False
		profileImg=''
		k = 0
		cat_local_display_name=''
		if( 'category_list' in tiktokProduct ):
			category_list = tiktokProduct['category_list']
			for i in category_list:
				print(f" We have found category {i['local_display_name'] }")
				cat_local_display_name = i['local_display_name']
				k=k+1
		new_product.tiktok_product_categories=cat_local_display_name
		array_of_images=False
		if( 'images' in tiktokProduct ):
			images=tiktokProduct['images']
			k=0
			array_of_images=[]
			for i in images:
				if( k==0 ):
					profileImg = i['thumb_url_list'][0]
				array_of_images.append(i['thumb_url_list'])
				k=k+1

		if( array_of_images ):
			del array_of_images[0]
			for addImg in array_of_images: 	
				new_product.append('additional_images',{
					"additional_image_src":addImg[0],
					"additional_image":addImg[0]
				})
		description=''
		if( 'description' in tiktokProduct ):
			description = tiktokProduct['description']
		brand_name=''
		if( 'brand' in tiktokProduct ):
			brand = tiktokProduct['brand']
			brand_name=brand['name']
		seller_sku='...'
		price=''
		l=0
		if( 'skus' in tiktokProduct ):
			for sku in tiktokProduct['skus']:
				seller_sku = sku['seller_sku']
				price = sku['price']
				price=price['original_price']
				if( 'sales_attributes' in sku ):
					sales_attributes = sku['sales_attributes']
					for j in sales_attributes:
						l=l+1
		if( l>1 ):
			is_variable=True
			seller_sku=''
		new_product.has_variants=is_variable
		new_product.product_name=tiktokProduct['product_name']
		new_product.erpnext_item_name=tiktokProduct['product_name']

		new_product.item_name=tiktokProduct['product_name']
		new_product.marketplace_id=tiktokProduct['product_id']
		new_product.brand=brand_name
		new_product.stock_keeping_unit_sku=seller_sku
		# new_product.disabled=tiktokProduct['product_id']
		# new_product.has_variants=tiktokProduct['product_id']
		new_product.profile_image_src=profileImg
		# new_product.additional_images=tiktokProduct['product_id']

		new_product.product_price=price

		# new_product.create_discount_campaign=tiktokProduct['product_id']

		new_product.long_description=description
		new_product.save(
			ignore_permissions=True, # ignore write permissions during insert
		)
		if( seller_sku=='' ):
			seller_sku="no-sku-"+str(tiktokProduct['product_id'])
		Item = frappe.db.exists("Item", str(seller_sku))
		if( Item == None ):
			self.create_product(tiktokProduct['product_name'],seller_sku,"By-product","no")
		return True

	def checkIfDocExistsWebhook( self,product_id ):
		print(f"product id is {product_id} ")
		return frappe.db.exists({"doctype": "Tiktok Products", "marketplace_id": product_id})



zav_country_map = {
	"AD": "Andorra",
	"AE": "United Arab Emirates",
	"AF": "Afghanistan",
	"AG": "Antigua and Barbuda",
	"AI": "Anguilla",
	"AL": "Albania",
	"AM": "Armenia",
	"AO": "Angola",
	"AQ": "Antarctica",
	"AR": "Argentina",
	"AS": "American Samoa",
	"AT": "Austria",
	"AU": "Australia",
	"AW": "Aruba",
	"AZ": "Azerbaijan",
	"BA": "Bosnia and Herzegovina",
	"BB": "Barbados",
	"BD": "Bangladesh",
	"BE": "Belgium",
	"BF": "Burkina Faso",
	"BG": "Bulgaria",
	"BH": "Bahrain",
	"BI": "Burundi",
	"BJ": "Benin",
	"BM": "Bermuda",
	"BR": "Brazil",
	"BS": "Bahamas",
	"BT": "Bhutan",
	"BV": "Bouvet Island",
	"BW": "Botswana",
	"BY": "Belarus",
	"BZ": "Belize",
	"CA": "Canada",
	"CF": "Central African Republic",
	"CH": "Switzerland",
	"CI": "Ivory Coast",
	"CK": "Cook Islands",
	"CL": "Chile",
	"CM": "Cameroon",
	"CN": "China",
	"CO": "Colombia",
	"CR": "Costa Rica",
	"CU": "Cuba",
	"CV": "Cape Verde",
	"CX": "Christmas Island",
	"CY": "Cyprus",
	"CZ": "Czech Republic",
	"DE": "Germany",
	"DJ": "Djibouti",
	"DK": "Denmark",
	"DM": "Dominica",
	"DO": "Dominican Republic",
	"DZ": "Algeria",
	"EC": "Ecuador",
	"EE": "Estonia",
	"EG": "Egypt",
	"EH": "Western Sahara",
	"ER": "Eritrea",
	"ES": "Spain",
	"ET": "Ethiopia",
	"FI": "Finland",
	"FJ": "Fiji",
	"FK": "Falkland Islands",
	"FM": "Micronesia",
	"FO": "Faroe Islands",
	"FR": "France",
	"GA": "Gabon",
	"GB": "United Kingdom",
	"GD": "Grenada",
	"GE": "Georgia",
	"GF": "French Guiana",
	"GG": "Guernsey",
	"GH": "Ghana",
	"GI": "Gibraltar",
	"GL": "Greenland",
	"GM": "Gambia",
	"GN": "Guinea",
	"GP": "Guadeloupe",
	"GQ": "Equatorial Guinea",
	"GR": "Greece",
	"GS": "South Georgia and the South Sandwich Islands",
	"GT": "Guatemala",
	"GU": "Guam",
	"GW": "Guinea-Bissau",
	"GY": "Guyana",
	"HK": "Hong Kong",
	"HM": "Heard Island and McDonald Islands",
	"HN": "Honduras",
	"HR": "Croatia",
	"HT": "Haiti",
	"HU": "Hungary",
	"ID": "Indonesia",
	"IE": "Ireland",
	"IL": "Israel",
	"IM": "Isle of Man",
	"IN": "India",
	"IO": "British Indian Ocean Territory",
	"IQ": "Iraq",
	"IR": "Iran",
	"IS": "Iceland",
	"IT": "Italy",
	"JE": "Jersey",
	"JM": "Jamaica",
	"JO": "Jordan",
	"JP": "Japan",
	"KE": "Kenya",
	"KG": "Kyrgyzstan",
	"KH": "Cambodia",
	"KI": "Kiribati",
	"KM": "Comoros",
	"KN": "Saint Kitts and Nevis",
	"KR": "Korea, Republic of",
	"KW": "Kuwait",
	"KY": "Cayman Islands",
	"KZ": "Kazakhstan",
	"LB": "Lebanon",
	"LC": "Saint Lucia",
	"LI": "Liechtenstein",
	"LK": "Sri Lanka",
	"LR": "Liberia",
	"LS": "Lesotho",
	"LT": "Lithuania",
	"LU": "Luxembourg",
	"LV": "Latvia",
	"LY": "Libya",
	"MA": "Morocco",
	"MC": "Monaco",
	"MD": "Moldova, Republic of",
	"ME": "Montenegro",
	"MG": "Madagascar",
	"MH": "Marshall Islands",
	"MK": "Macedonia",
	"ML": "Mali",
	"MM": "Myanmar",
	"MN": "Mongolia",
	"MO": "Macao",
	"MP": "Northern Mariana Islands",
	"MQ": "Martinique",
	"MR": "Mauritania",
	"MS": "Montserrat",
	"MT": "Malta",
	"MU": "Mauritius",
	"MV": "Maldives",
	"MW": "Malawi",
	"MX": "Mexico",
	"MY": "Malaysia",
	"MZ": "Mozambique",
	"NA": "Namibia",
	"NC": "New Caledonia",
	"NE": "Niger",
	"NF": "Norfolk Island",
	"NG": "Nigeria",
	"NI": "Nicaragua",
	"NL": "Netherlands",
	"NO": "Norway",
	"NP": "Nepal",
	"NR": "Nauru",
	"NU": "Niue",
	"NZ": "New Zealand",
	"OM": "Oman",
	"PA": "Panama",
	"PE": "Peru",
	"PF": "French Polynesia",
	"PG": "Papua New Guinea",
	"PH": "Philippines",
	"PK": "Pakistan",
	"PL": "Poland",
	"PM": "Saint Pierre and Miquelon",
	"PN": "Pitcairn",
	"PR": "Puerto Rico",
	"PT": "Portugal",
	"PW": "Palau",
	"PY": "Paraguay",
	"QA": "Qatar",
	"RO": "Romania",
	"RS": "Serbia",
	"RU": "Russian Federation",
	"RW": "Rwanda",
	"SA": "Saudi Arabia",
	"SB": "Solomon Islands",
	"SC": "Seychelles",
	"SD": "Sudan",
	"SE": "Sweden",
	"SG": "Singapore",
	"SI": "Slovenia",
	"SJ": "Svalbard and Jan Mayen",
	"SK": "Slovakia",
	"SL": "Sierra Leone",
	"SM": "San Marino",
	"SN": "Senegal",
	"SO": "Somalia",
	"SR": "Suriname",
	"ST": "Sao Tome and Principe",
	"SV": "El Salvador",
	"SY": "Syria",
	"SZ": "Swaziland",
	"TC": "Turks and Caicos Islands",
	"TD": "Chad",
	"TF": "French Southern Territories",
	"TG": "Togo",
	"TH": "Thailand",
	"TJ": "Tajikistan",
	"TK": "Tokelau",
	"TM": "Turkmenistan",
	"TN": "Tunisia",
	"TO": "Tonga",
	"TR": "Turkey",
	"TT": "Trinidad and Tobago",
	"TV": "Tuvalu",
	"TW": "Taiwan",
	"TZ": "Tanzania",
	"UA": "Ukraine",
	"UG": "Uganda",
	"UM": "United States Minor Outlying Islands",
	"US": "United States",
	"UY": "Uruguay",
	"UZ": "Uzbekistan",
	"VC": "Saint Vincent and the Grenadines",
	"VE": "Venezuela, Bolivarian Republic of",
	"VN": "Vietnam",
	"VU": "Vanuatu",
	"WF": "Wallis and Futuna",
	"WS": "Samoa",
	"YE": "Yemen",
	"YT": "Mayotte",
	"ZA": "South Africa",
	"ZM": "Zambia",
	"ZW": "Zimbabwe",
}
