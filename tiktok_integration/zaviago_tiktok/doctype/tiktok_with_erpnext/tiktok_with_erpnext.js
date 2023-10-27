// Copyright (c) 2023, Zaviago and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tiktok with ERPnext', {
	// refresh: function(frm) {
	// 	if( frm.doc.enable_tiktok){
	// 		frm.add_custom_button("Create/Refresh Connection",()=>{
	// 			frappe.msgprint("Try Connection");	
	// 		})
	// 	}
	update_tiktok_shop_product:function(frm){
		frappe.prompt([
			{
				fieldname: 'web_item',
				label: __('Select Item'),
				fieldtype: 'Link',
				options: 'Tiktok Item',  
				reqd: 1,
			},
		], function(values){
			frappe.call({
				method: 'tiktok_integration.zaviago_tiktok.doctype.tiktok_with_erpnext.api.updateTiktokProduct',
				args: {
					'web_item': values.web_item,
				},
				callback: function(r){
					if(r.message) {
					   console.log(r.message);
					}
				}
			});
		}, __('Update'), 'Submit');
	},
	start_connection:function(frm){
		// frappe.msgprint("test") 
		// return
		if( !frm.doc.enable_tiktok){
			frappe.msgprint("Please enable tiktok api")
			return
		}
		if( frm.doc.app_key =='' ){
			frappe.msgprint("Please add tiktok app key")
			return
		}
		if( frm.doc.app_secret =='' ){
			frappe.msgprint("Please add tiktok app secret")
			return
		}
		frappe.call({
			method: "tiktok_integration.zaviago_tiktok.create_client.redirect_to_auth",
			type: "POST",
			freeze: true,
			freeze_message: "Redirecting...",
			callback:function(r){
				if( r.message.url != null )
					window.location = r.message.url;

			}
		});
	},
	fetch_orders:function(frm){
		
		if( !frm.doc.enable_tiktok){
			frappe.msgprint("Please enable tiktok api")
			return
		}
		if( frm.doc.app_key =='' ){
			frappe.msgprint("Please add tiktok app key")
			return
		}
		if( frm.doc.app_secret =='' ){
			frappe.msgprint("Please add tiktok app secret")
			return
		}
		if( frm.doc.access_token =='' ){
			frappe.msgprint("Please start connection to get accesstoken")
			return
		}
		frappe.call({
			method: "tiktok_integration.zaviago_tiktok.doctype.tiktok_with_erpnext.tiktok_with_erpnext.ajax_init_fetch_orders",
			type: "POST",
			args: {},
			success: function(r) {
			},
			error: function(r) {},
			always: function(r) {},
			freeze: true,
			freeze_message: "Fetching Orders...",
			
		});
	},
	fetch_products:function(frm){
		if( !frm.doc.enable_tiktok){
			frappe.msgprint("Please enable tiktok api")
			return
		}
		if( frm.doc.app_key =='' ){
			frappe.msgprint("Please add tiktok app key")
			return
		}
		if( frm.doc.app_secret =='' ){
			frappe.msgprint("Please add tiktok app secret")
			return
		}
		if( frm.doc.access_token =='' ){
			frappe.msgprint("Please start connection to get accesstoken")
			return
		}
		frappe.call({
			method: "tiktok_integration.zaviago_tiktok.doctype.tiktok_with_erpnext.tiktok_with_erpnext.ajax_init_fetch_products",
			type: "POST",
			freeze: true,
			freeze_message: "Fetching Products...",
			callback:function(r){
				console.log(r)
			}
			
		}); 
	},sync_categories:function(frm){
		if( !frm.doc.enable_tiktok){
			frappe.msgprint("Please enable tiktok api")
			return
		}
		if( frm.doc.app_key =='' ){
			frappe.msgprint("Please add tiktok app key")
			return
		}
		if( frm.doc.app_secret =='' ){
			frappe.msgprint("Please add tiktok app secret")
			return
		}
		if( frm.doc.access_token =='' ){
			frappe.msgprint("Please start connection to get accesstoken")
			return
		}
		frappe.call({
			async: true,
			method: "tiktok_integration.zaviago_tiktok.doctype.tiktok_with_erpnext.api.fetch_categories",
			type: "POST",
			freeze: true,
			freeze_message: "Synchronizing categories...",
			callback:function(r){
				if( r.message != undefined ){
					
					    // options=[]
						// r.message.forEach((element) => {
						// 	var arr2 = [{ value: element.id, label: element.local_display_name }];
						// 	options.push(...arr2);
						//   });
						// console.log(doc)
						

					
				}
			},
		});
	},

});
