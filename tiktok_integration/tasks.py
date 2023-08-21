import frappe
from tiktok_integration.zaviago_tiktok.create_client import CreateTiktokClient

def daily():
    tiktokClient = CreateTiktokClient()
    tiktokClient.refreshToken()
    return
