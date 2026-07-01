import os
import sqlite3
import logging
from pathlib import Path

QUERY_DIR = Path("../../../sql")
COUNT_TOTAL_CARDS = QUERY_DIR / "count_total_cards.sql"
COUNT_CARDS = QUERY_DIR / "count_cards.sql"
COUNT_CATEGORIES = QUERY_DIR / "count_categories.sql"

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s | %(message)s"
)


def run_data_profile(db_path):
	if not input_db_isValid(db_path):
		return
	stats = get_data_profile_stats(db_path)
	if stats is not None:
		print_data_profile_report(stats)


def input_db_isValid(db_path):
	if not os.path.isfile(db_path):
		logging.error(f"Database not found: {db_path}")
		return False
	if not os.access(db_path, os.R_OK):
		logging.error(f"Database not readable: {db_path}")
		return False
	return True


def get_data_profile_stats(db_path):
	stats = {
		"total_records":0,
		"card_counts":{},
		"category_counts":{}
	}
	try:
		with sqlite3.connect(db_path) as conn:
			cursor = conn.cursor()
			cursor.execute(COUNT_TOTAL_CARDS.read_text(encoding="utf-8"))
			stats["total_records"] = cursor.fetchone()[0]

			cursor.execute(COUNT_CARDS.read_text(encoding="utf-8"))
			for row in cursor.fetchall():
				stats["card_counts"][row[0]] = row[1]

			cursor.execute(COUNT_CATEGORIES.read_text(encoding="utf-8"))
			row = cursor.fetchone()
			col = [description[0] for description in cursor.description]
			stats["category_counts"] = dict(zip(col, row))

	except sqlite3.Error as code:
		logging.error(f"Profile Error: {code}")
		return None
	return stats


def print_data_profile_report(stats):
	print(
		f"--- 🔍 DATA REPORT ---"
		f"\n📊 Total Records: {stats['total_records']}\n"
		f"\n💳 Card Counts:"
	)
	for bank, count in stats["card_counts"].items():
		print(f"  - {bank}: {count}")
	print("\n🏷️ Category Counts:")
	for category, count in stats["category_counts"].items():
		print(f"  - {category}: {count}")