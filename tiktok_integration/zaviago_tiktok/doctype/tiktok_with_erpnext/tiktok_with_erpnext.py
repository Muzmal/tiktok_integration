# Copyright (c) 2023, Zaviago and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from tiktok_integration.zaviago_tiktok.create_client import CreateTiktokClient
import webbrowser
from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData
import json
import unicodedata
import calendar;
import time;
import hashlib
import hmac
import binascii
from datetime import datetime
from PIL import Image
import random
from frappe.utils.file_manager import save_file
import time

from frappe.utils import cstr, flt, cint, get_files_path

class TiktokwithERPnext(Document):
	def validate(self):
		
			return
	# pass

class handleTiktokRequests:
	next_cursor=False
	limit = 10
	added_orders=0
	app_details = frappe.get_doc('Tiktok with ERPnext')
	if( app_details.enable_tiktok == True ):
		if( app_details.maximum_orders_to_fetch and app_details.maximum_orders_to_fetch<=100 ):
			max_number=app_details.maximum_orders_to_fetch
		else:
			max_number = 100

	def save_tiktok_order(self,orders):
		for o in orders: 
			if( self.added_orders >= self.max_number ):
				break
			prev_order = frappe.db.exists({"doctype": "Sales Order", "tiktok_order_id": o['order_id']})
			if( prev_order ):
				print(f"\n\n Order is already saved {prev_order}: {o['order_id']} \n\n")
				continue
			new_order = frappe.new_doc('Sales Order')
			# if o.get("shipping_provider") is not None:
			# 	return
			# print(f"Please Check Order Details {o}")
			customer_flag = frappe.db.exists("Customer", o['recipient_address']['name'] )
			if( customer_flag ==None ):
				self.create_customer( o['recipient_address'],o['recipient_address']['name'] )
			new_order.title=o['recipient_address']['name']
			new_order.customer=o['recipient_address']['name']
			new_order.order_type="Sales"
			date = o['create_time']
			
			date = int(date)/1000
			date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d') 
			new_order.delivery_date=date
			new_order.transaction_date=date
			new_order.tiktok_order_id=o['order_id']
			save_order_class=saveTiktokData()
			# new_order.marketplace_name="Tiktok"
			new_order.marketplace="Tiktok"
			new_order.marketplace_order_number=o['order_id']

			new_order.tiktok_order_status = save_order_class.fetchStatusFromCode(o['order_status'])
			# add status here
			
			new_order.price_list_currency=o['payment_info']['currency']
			# create property setter for length

			for product in o['item_list']:
				if( product['seller_sku'] =='' ):
						product['seller_sku']="no-sku-"+str(product['product_id'])
				item_code = product['seller_sku']
				Item = frappe.db.exists("Item", str(item_code))
				if( Item == None ):
					self.create_product(product['product_name'],product['seller_sku'],"By-product","no")
					p_img = save_order_class.fetchProduct( product['product_id'],return_image=True )
					if( p_img ):
							print(f" Got product image { p_img }")
							save_order_class.addImageToItem(p_img,product['seller_sku'])
					ifExist=self.checkIfDocExists( product['product_id'] )
					return str(product['product_id']) + "test"
					if( ifExist == None ):	
						self.saveTiktokProduct( product )
					
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
					shipping = frappe.db.exists("Item", str('item_shipping_cost'))
					if( shipping == None ):	
		
						self.create_product(product['product_name'],product['seller_sku'],"By-product","yes")
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
			save_order_class._save_sales_invoice(o)
			# frappe.msgprint("Created order")
			self.added_orders=self.added_orders+1
		return
	
	def create_customer(self,order_address,customer_name):
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
		frappe.db.commit()
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
		frappe.db.commit()
		new_customer = frappe.new_doc('Customer')
		new_customer.customer_name=customer_name
		new_customer.customer_group="Tiktok"
		new_customer.territory="Thailand"
		response = new_customer.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		# frappe.msgprint("Created customer")
		frappe.db.commit()
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
		).insert(ignore_mandatory=True)
		frappe.db.commit()

	def create_product(self,item_name,item_code,item_group,is_shipping):
		item_group="Tiktok"
		if( is_shipping=='yes' ):
			item_name='shipping'
			item_code='item_shipping_cost'
		item = frappe.new_doc('Item')
		item.item_name=item_name
		item.item_code=item_code
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

		item.item_group="Tiktok"
		response = item.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		frappe.db.commit()
		return
	@frappe.whitelist( )
	def fetch_orders(self):
		 
		path='/api/orders/search'
		app_details = frappe.get_doc('Tiktok with ERPnext')
		access_token = app_details.get_password('access_token')
		app_secret = app_details.get_password('app_secret')
		gmt = time.gmtime()
		timestamp = calendar.timegm(gmt)    
		query = {
			"app_key":app_details.app_key,
			'access_token':access_token,
			'limit':20,
			'timestamp':timestamp,
		}
		params_for_sign = query
		del params_for_sign['access_token']
		##################################
		signature = self.getSignature(path,params_for_sign,app_secret)
		##################################
		if( app_details.is_sandbox ):
			uri = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			uri = 'https://open-api.tiktokglobalshop.com'
		url = uri+"/api/orders/search?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&limit=20&sign="+str(signature)+"&timestamp="+str(timestamp)
		if( self.next_cursor ):
			json_params={
				'cursor':self.next_cursor,
				"page_size": 50
			}
		else:
			json_params={
				"page_size": 50
			}
		payload = json.dumps( json_params )
		headers = {
		'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		data = response.json()
		if( data['code']==0 ):
			print(f"\n\n {data['data']} ")
			order_list=[]
			if ( 'order_list' in data['data'] ) :
				for order in data['data']['order_list']:
					order_list.append(order['order_id'])
			self.fetchOrderDetails(order_list)
			if( data['data']['more']==True ):
				print(f"\n\n next cursor is {data['data']['next_cursor']} \n\n")
				self.next_cursor=data['data']['next_cursor']
			else:
				self.next_cursor=False
		else:
			print(f"\n\n {response} ")
		return

	def fetchOrderDetails(self,orderIDs):
		############################### get order details
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
		signature = self.getSignature(path,params_for_sign,app_secret)
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
			order = data['data']['order_list']
			self.save_tiktok_order(data['data']['order_list'])
		return 


	def getSignature( self,path,params,app_secret ):
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
	

	def fetchProducts( self ):
		path='/api/products/search'
		
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
		
		params_for_sign = query
		del params_for_sign['access_token']
		##################################
		signature = self.getSignature(path,params_for_sign,app_secret)
		##################################
		if( app_details.is_sandbox ):
			uri = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			uri = 'https://open-api.tiktokglobalshop.com'
		url = uri+path+"?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&sign="+str(signature)+"&timestamp="+str(timestamp)
		json_params={
			'page_number':1,
			"page_size": 50
		}
		
		payload = json.dumps( json_params )
		headers = {
		'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		data = response.json()
		products= data['data']
		
		if( data['code']==0 ):
			save_data = saveTiktokData()
			for product in products['products']:
				ifExist=self.checkIfDocExists( product['id'] )
				if( ifExist == None ):	
					tiktokProduct=save_data.fetchProduct( product['id'],False )
					self.saveTiktokProduct( tiktokProduct )

				
					
		else:
			print(f"\n\n {response} ")
		return
		
	
	def saveTiktokProduct( self,tiktokProduct ):
		
		print("product does not Exist")
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

	def checkIfDocExists( self,product_id ):
		print(f"product id is {product_id} ")
		return frappe.db.exists({"doctype": "Tiktok Products", "marketplace_id": product_id})

		

@frappe.whitelist( )
def ajax_init_fetch_orders():
	app_details = frappe.get_doc('Tiktok with ERPnext')
	if( app_details.enable_tiktok == True ):
		if( app_details.maximum_orders_to_fetch and app_details.maximum_orders_to_fetch<=100 ):
			max_number=app_details.maximum_orders_to_fetch
		else:
			max_number = 100
		print(f" max_number is  {max_number} ")
		
		tiktok = handleTiktokRequests()
		tiktok.fetch_orders( )
		count= 1 
		while( tiktok.next_cursor and tiktok.added_orders <= max_number ):
			print(f" tiktok.added_order is  {tiktok.added_orders} ")
			# return
			count=count+1
			print(f"\n\n next cursor is set {count} added orders are {tiktok.added_orders}")
			tiktok.fetch_orders()
		url = frappe.utils.get_url()+"app/sales-order"
		print(f"\n\n url is {url} ")
		webbrowser.open( url,new=0 )
	else:
		frappe.throw("Please Enable Tiktok to start fetching orders")
	return

@frappe.whitelist( )
def ajax_init_fetch_products():
	app_details = frappe.get_doc('Tiktok with ERPnext')
	if( app_details.enable_tiktok == True ):
		tiktok = handleTiktokRequests()
		response = tiktok.fetchProducts()
	else:
		frappe.throw("Please Enable Tiktok to start fetching products")
	return response

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
