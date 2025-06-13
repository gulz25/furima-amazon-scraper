import csv
import time
import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def load_defaults(filepath="default.txt"):
    defaults = {
        "除外キーワード": "",
        "最小販売価格": "1000",
        "商品状態": "新品、未使用",
        "発送負担": "指定なし",
        "is_enable": "1",
        "累計件数": "0",
        "３０日件数": "0",
        "削除": "0"
    }
    with open(filepath, encoding="shift-jis") as f:
        for line in f:
            if ":" not in line:
                continue
            key, value = line.strip().lstrip("#").split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if key in defaults:
                defaults[key] = value
    return defaults

def search_amazon(keyword):
    url = f"https://www.amazon.co.jp/s?k={requests.utils.quote(keyword)}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"HTTPエラー: {response.status_code}")
        return None, None, None

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select("div.s-main-slot div[data-asin][data-component-type='s-search-result']")

    keyword_normalized = re.sub(r"\s+", "", keyword).lower()
    selected = None
    for result in results:
        title_elem = result.select_one("h2 span")
        title = title_elem.text.strip() if title_elem else ""
        if keyword_normalized in re.sub(r"\s+", "", title).lower():
            selected = result
            break

    if not selected and results:
        selected = results[0]

    if not selected:
        return None, None, None

    title = selected.select_one("h2 span").text.strip() if selected.select_one("h2 span") else None
    asin = selected.get("data-asin")

    price_block = selected.select_one("span.a-price > span.a-offscreen")
    if price_block:
        try:
            price_str = price_block.text.strip().replace("￥", "").replace(",", "")
            price = int(float(price_str))
        except:
            price = None
    else:
        price = None

    return title, price, asin

def main():
    defaults = load_defaults()

    with open("input.csv", newline='', encoding="shift-jis") as infile, \
         open("output.csv", mode="w", newline='', encoding="shift-jis") as outfile, \
         open("nodata.csv", mode="w", newline='', encoding="shift-jis") as errorfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        error_writer = csv.writer(errorfile)

        headers_row = next(reader)
        writer.writerow(headers_row)
        error_writer.writerow(headers_row)

        for i, row in enumerate(reader, 1):
            keyword = row[2].strip()  # 検索キーワード

            print(f"{i}. Amazon検索: {keyword} ...")
            title, price, asin = search_amazon(keyword)

            if title and price and asin:
                row[1] = title  # アラート名
                row[3] = defaults["除外キーワード"]
                row[4] = defaults["最小販売価格"]
                row[5] = int(price * 0.77)  # 最高販売価格
                row[6] = defaults["商品状態"]
                row[7] = defaults["発送負担"]
                row[8] = asin
                row[9] = defaults["is_enable"]
                row[10] = defaults["累計件数"]
                row[11] = defaults["３０日件数"]
                row[12] = defaults["削除"]
                writer.writerow(row)
                print(f"    → 成功: {title} / ¥{price} / {asin}")
            else:
                error_writer.writerow(row)
                print("    → 取得失敗（nodata.csvに記録）")

            time.sleep(5)

if __name__ == "__main__":
    main()
