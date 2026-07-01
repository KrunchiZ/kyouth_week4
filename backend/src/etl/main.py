import os
import sys
from pathlib import Path
from ingestor import ingest_all_mhtml
from processor import process_all_html
from loader import load_all_jsons
from profiler import run_data_profile
from dotenv import load_dotenv

load_dotenv()
DEV = os.getenv("DEV") == "true"
SOURCE_DIR = Path("../../data/0_source") if DEV else Path("/app/data/0_source")
BRONZE_DIR = Path("../../data/1_bronze") if DEV else Path("/app/data/1_bronze")
SILVER_DIR = Path("../../data/2_silver") if DEV else Path("/app/data/2_silver")
GOLD_DIR = Path("../../data/3_gold") if DEV else Path("/app/data/3_gold")
DB_NAME = "credit_cards.db"


def run_profiler():
	run_data_profile(GOLD_DIR / DB_NAME)

def run_gold():
	print("🥇 Gold: Loading data...")
	load_all_jsons(SILVER_DIR, GOLD_DIR)

def run_silver():
	print("🥈 Silver: Processing data...")
	process_all_html(BRONZE_DIR, SILVER_DIR)

def run_bronze():
	print("🥉 Bronze: Ingesting data...")
	ingest_all_mhtml(SOURCE_DIR, BRONZE_DIR)

def run_all():
	run_bronze()
	run_silver()
	run_gold()
	run_profiler()


def main():
	if len(sys.argv) != 2:
		print("Usage: python main.py [ingest|process|load|profile|all]")
		return
		
	commands = {
		"ingest":   run_bronze,
		"process":  run_silver,
		"load":     run_gold,
		"profile":  run_profiler,
		"all":      run_all
	}    
	if sys.argv[1] not in commands:
		print("Usage: python main.py [ingest|process|load|profile|all]")
		return

	commands[sys.argv[1]]()


if __name__ == "__main__":
	main()
