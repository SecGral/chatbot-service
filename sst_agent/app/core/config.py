#Este archivo centraliza configuración.
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = "SST Agent"
VERSION = "0.1"
DEBUG = True

HF_TOKEN = os.getenv("HF_TOKEN", "")
