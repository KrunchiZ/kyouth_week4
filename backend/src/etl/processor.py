import os
import re
import logging
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, Field

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s | %(message)s"
)

class CreditCard(BaseModel):
	card_title			: str = Field(min_length=1)
	bank				: str = Field(min_length=1)
	cashback			: str = Field(min_length=1)
	petrol				: str = Field(min_length=1)
	rewards				: str = Field(min_length=1)
	travel				: str = Field(min_length=1)
	premium_perks		: str = Field(min_length=1)
	balance_transfer	: str = Field(min_length=1)
	easy_payment_plan	: str = Field(min_length=1)
	fees				: str = Field(min_length=1)
	requirements		: str = Field(min_length=1)
	features			: str = Field(min_length=1)

BANK_NAMES = [
	"AEON",
	"Affin",
	"Alliance Bank",
	"AmBank",
	"Bank Islam",
	"Bank Rakyat",
	"BSN",
	"CIMB",
	"HSBC",
	"Hong Leong",
	"Maybank",
	"OCBC",
	"Public Bank",
	"RHB",
	"Standard Chartered",
	"UOB"
]


def process_all_html(input_dir, output_dir):
	if not input_dir_isValid(input_dir):
		return
	if not init_output_dir(output_dir):
		return    

	process_count = 0
	for html_file in input_dir.glob("*.html"):
		try:
			with open(html_file, "r", encoding="utf-8") as in_file:
				soup = BeautifulSoup(in_file, "html.parser")
				card_title = (soup.find("meta", property="og:title")["content"])
				bank = get_bank_name(card_title)
				petrol = get_soup_text(soup, "petrol")
				cashback = get_soup_text(soup, "cashback")
				rewards = get_soup_text(soup, "rewards")
				travel = get_soup_text(soup, "travel")
				premium_perks = get_soup_text(soup, "premium")
				balance_transfer = get_soup_text(soup, "balance-transfer")
				easy_payment_plan = get_soup_text(soup, "easy-payment-plan")
				fees = get_soup_text(soup, "fees")
				requirements = get_soup_text(soup, "requirements")
				features = get_soup_text(soup, "features")
		except Exception as code:
			logging.error(f"Error processing {html_file.name}: {code}")
			continue

		try:
			output_data = CreditCard(
				card_title = card_title,
				bank = bank,
				cashback = cashback,
				petrol = petrol,
				rewards = rewards,
				travel = travel,
				premium_perks = premium_perks,
				balance_transfer = balance_transfer,
				easy_payment_plan = easy_payment_plan,
				fees = fees,
				requirements = requirements,
				features = features,
			)
			output_path = output_dir / (html_file.stem + ".json")
			with open(output_path, "w", encoding="utf-8") as out_file:
				out_file.write(output_data.model_dump_json(indent=2))
				logging.info(f"Processed: {html_file.name}")
				process_count += 1

		except ValidationError as code:
			for error in code.errors():
				logging.error(f"Missing {error['loc'][0].strip()} "
							  f"in {html_file.name}")
		except Exception as code:
			logging.error(f"{code}: {html_file.name}")

	total_count = len(list(input_dir.glob("*.html")))
	print(f"\n📊 Silver Summary:\nTotal: {total_count} | Processed: "
		  f"{process_count} | Skipped: {total_count - process_count}")


def input_dir_isValid(input_dir):
	if not input_dir.exists():
		logging.warning(f"Input directory not found: {input_dir}")
		return False
	if not os.access(input_dir, os.R_OK):
		logging.warning(f"Input directory not readable: {input_dir}")
		return False
	return True


def init_output_dir(output_dir):
	try:
		output_dir.mkdir(parents=True, exist_ok=True)
		return True
	except Exception as code:
		logging.error(f"{code}: {output_dir}")
		return False


def get_bank_name(card_title):
	for bank in BANK_NAMES:
		if bank.lower() in card_title.lower():
			return bank
	return None


def get_soup_text(soup, attr_value):
	tag = soup.find(attrs={"id": attr_value})
	if tag is None:
		if (attr_value == "card_title" or attr_value == "bank"
	  			or attr_value == "fees" or attr_value == "requirements"
				or attr_value == "review"):
			return None
		else:
			return "N/A"
	value: str = get_all_elements_text(tag)
	if value == "" or value.lower().strip() == attr_value.lower():
		if (attr_value == "card_title" or attr_value == "bank"
	  			or attr_value == "fees" or attr_value == "requirements"
				or attr_value == "review"):
			return None
		else:
			return "N/A"
	return value


def get_all_elements_text(tag) -> str:
	value: str = ""
	for element in tag.find_all(recursive=False):
		if element.name == "small" or element.name == "button":
			continue
		elif element.name == "table":
			value += get_table_text(element) + "\n"
		elif element.name == "div" and "table-wrapper" in element.get("class", []):
			value += get_table_text(element.find("table")) + "\n"
		else:
			value += element.get_text(separator=" ", strip=True) + "\n"
	return sanitize_text(value)


def get_table_text(tag) -> str:
	caption = tag.find("caption")
	value: str = "\n# " + caption.get_text(separator=" ", strip=True) + "\n" if caption else ""
	value += table_to_markdown(tag)
	return value


def table_to_markdown(table) -> str:
	markdown: list[str] = []
	
	headers = [th.get_text(separator=" ", strip=True) for th in table.find_all("th")]
	if headers:
		markdown.append("| " + " | ".join(headers) + " |")
		markdown.append("|" + "|".join(["---"] * len(headers)) + "|")
	
	for row in table.find_all("tr"):
		cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
		if cells:
			if not markdown:
				markdown.append(
					"| " + " | ".join([f"Column {i+1}" for i in range(len(cells))]) + " |"
				)
				markdown.append("|" + "|".join(["---"] * len(cells)) + "|")
			markdown.append("| " + " | ".join(cells) + " |")
	return "\n".join(markdown)


def sanitize_text(text: str) -> str:
	text = text.replace("\u2013", "-")
	text = text.replace("\x00", "").replace("\0", "")
	text = re.sub(r'[\u2018\u2019]', "'", text)
	text = re.sub(r'[\xa0\u200b\u200c\u200d]', ' ', text)
	text = re.sub(r'[ \t]+', ' ', text)
	return text.strip()