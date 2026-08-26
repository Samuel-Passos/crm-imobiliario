import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
# Need postgres connection to alter table!
# But since we have no postgres string, I can't easily ALTER TABLE via python.
