import sys
sys.path.append('../')
from ADC_function import *
from WebCrawler.crawler import *
import re
import time
from urllib.parse import quote

JSON_HEADERS = {"Referer": "https://dl.getchu.com/"}
COOKIES_DL = {"adult_check_flag": "1"}
COOKIES_WWW = {'getchu_adalt_flag': 'getchu.com'}

# GETCHU_WWW_SEARCH_URL = 'http://www.getchu.com/php/search.phtml?genre=anime_dvd&search_keyword=_WORD_&check_key_dtl=1&submit='
# GETCHU_DL_SEARCH_URL = 'https://dl.getchu.com/search/search_list.php?dojin=1&search_category_id=&search_keyword=_WORD_&btnWordSearch=%B8%A1%BA%F7&action=search&set_category_flag=1'
GETCHU_WWW_URL = 'http://www.getchu.com/soft.phtml?id=_WORD_'
GETCHU_DL_URL = 'https://dl.getchu.com/i/'

def get_dl_getchu(number):
    url =  GETCHU_DL_URL+ number
    print("[+]DEBUG-dl_getchu:", url)
    htmlcode = get_html(url, json_headers=JSON_HEADERS, cookies=COOKIES_DL)                            
    getchu = Crawler(htmlcode)
    dic = {
        "title": getchu.getString("//div[contains(@style,'color: #333333; padding: 3px 0px 0px 5px;')]/text()"),
        "cover": "https://dl.getchu.com" + getchu.getString("//td[contains(@bgcolor,'#ffffff')]/img/@src"),
        "director": getchu.getString("//td[contains(text(),'作者')]/following-sibling::td/text()").strip(),
        "studio": getchu.getString("//td[contains(text(),'サークル')]/following-sibling::td/a/text()").strip(),
        "actor": getchu.getString("//td[contains(text(),'サークル')]/following-sibling::td/a/text()").strip(),
        "label": getchu.getString("//td[contains(text(),'サークル')]/following-sibling::td/a/text()").strip(),
        "runtime": str(re.findall(r'\d+', str(getchu.getString(
            "//td[contains(text(),'画像数&ページ数')]/following-sibling::td/text()")))).strip(" ['']"),
        "release": getchu.getString("//td[contains(text(),'配信開始日')]/following-sibling::td/text()").replace("/", "-"),
        "tag": getchu.getStrings("//td[contains(text(),'趣向')]/following-sibling::td/a/text()"),
        "outline": getOutline(getchu, ['作品紹介', 'ストーリー', 'あらすじ', '商品紹介'], "//div[contains(text(),'{keyword}')]/following-sibling::div/text()".strip()),
        "extrafanart": getchu.getStrings("//td[contains(@style,'background-color: #444444;')]/a/@href"),
        "series": getchu.getString("//td[contains(text(),'サークル')]/following-sibling::td/a/text()"),
        "number": number,
        "imagecut": 4,
        "year": str(re.findall(r'\d{4}', str(getchu.getString(
            "//td[contains(text(),'配信開始日')]/following-sibling::td/text()").replace("/", "-")))).strip(" ['']"),
        "actor_photo": "",
        "website": "https://dl.getchu.com/i/" + number,
        "source": "getchu.py",
        "allow_number_change": True,
    }
    extrafanart = []
    for i in dic['extrafanart']:
        i = "https://dl.getchu.com" + i
        extrafanart.append(i)
    dic['extrafanart'] = extrafanart
    time.sleep(1)
    return dic

def get_www_getchu(number):
    getchu_number = quote(number.upper().replace("GETCHU-", ""), encoding="euc_jp")
    url = GETCHU_WWW_URL.replace("_WORD_", getchu_number) + "&gc=gc"
    print("[+]DEBUG-www_getchu:", url)
    getchu = Crawler(get_html(url, cookies=COOKIES_WWW))
    dic = {
        "title": getchu.getString('//*[@id="soft-title"]/text()').strip(),
        "cover": "http://www.getchu.com" + getchu.getString(
            "/html/body/div[1]/table[2]/tr[1]/td/a/@href").replace("./", '/'),
        "director": getchu.getString("//td[contains(text(),'ブランド')]/following-sibling::td/a[1]/text()"),
        "studio": getchu.getString("//td[contains(text(),'サークル：')]/following-sibling::td/a[1]/text()").strip().replace("（このサークルの作品一覧）",""),
        "actor": getchu.getString("//td[contains(text(),'ブランド')]/following-sibling::td/a[1]/text()").strip(),
        "label": getchu.getString("//td[contains(text(),'ジャンル：')]/following-sibling::td/text()").strip(),
        "runtime": '',
        "release": getchu.getString("//td[contains(text(),'発売日：')]/following-sibling::td/a/text()").replace("/", "-").strip(),
        "tag": [tag for tag in getchu.getStrings("//td[contains(text(),'カテゴリ')]/following-sibling::td/a/text()") if tag != "[一覧]"],
        "outline": getOutline(getchu),
        "extrafanart": getchu.getStrings("//div[contains(text(),'サンプル画像')]/following-sibling::div/a/@href"),
        "series": getchu.getString("//td[contains(text(),'ジャンル：')]/following-sibling::td/text()").strip(),
        "number": number,
        "imagecut": 0,
        "year": str(re.findall(r'\d{4}', str(getchu.getString(
            "//td[contains(text(),'発売日：')]/following-sibling::td/a/text()").replace("/", "-")))).strip(" ['']"),
        "actor_photo": "",
        "website": url,
        "headers": {'referer': url},
        "source": "getchu.py",
        "allow_number_change": True,
    }
    extrafanart = []
    for i in dic['extrafanart']:
        i = "http://www.getchu.com" + i.replace("./", '/')
        if 'jpg' in i:
            extrafanart.append(i)
    dic['extrafanart'] = extrafanart
    time.sleep(1)
    return dic

def getOutline(crawler):
    """
    获取outline内容
    查找class名称为tabletitle_1、tabletitle_2等的div，获取其下的tablebody内容中的bootstrap span文本
    并对获取的文本进行strip()处理，去掉多余的空格
    :param crawler: Crawler实例
    :return: 获取到的内容列表
    """
    # 尝试1: 直接查找作品紹介对应的tablebody中的bootstrap span内容
    result = crawler.getStrings("//div[contains(text(), '作品紹介')]/following-sibling::div[contains(@class, 'tablebody')]/span[contains(@class, 'bootstrap')]/text()")
    if result:
        # 对文本进行strip()处理并过滤空字符串
        return [text.strip() for text in result if text.strip()]
    
    # 尝试2: 查找所有tablebody中的bootstrap span内容
    result = crawler.getStrings("//div[contains(@class, 'tablebody')]/span[contains(@class, 'bootstrap')]/text()")
    if result:
        # 对文本进行strip()处理并过滤空字符串
        return [text.strip() for text in result if text.strip()]
    
    # 尝试3: 查找所有tabletitle后的tablebody内容(包括子节点的文本)
    result = crawler.getStrings("//div[contains(@class, 'tabletitle')]/following-sibling::div[contains(@class, 'tablebody')]//text()")
    if result:
        # 过滤掉空字符串和纯空格的内容
        return [text.strip() for text in result if text.strip()]
    
    # 尝试4: 查找包含作品紹介的div后的所有文本内容
    result = crawler.getStrings("//div[contains(text(), '作品紹介')]/following-sibling::div//text()")
    if result:
        return [text.strip() for text in result if text.strip()]
    
    # 尝试5: 回退到原始方法
    keywords = ['作品紹介', 'ストーリー', 'あらすじ', '商品紹介']
    for keyword in keywords:
        xpath = "//div[contains(text(), '{keyword}')]/following-sibling::div//text()".format(keyword=keyword)
        result = crawler.getStrings(xpath)
        filtered_result = [text.strip() for text in result if text.strip()]
        if filtered_result:
            return filtered_result
    
    return []

def main(number):
    number = number.replace("-C", "")
    
    print("[+]DEBUG-getchu: number = " + number)

    dic = {}
    if "GETCHU" in number.upper():
        # sort = ["get_dl_getchu(number)", "get_www_getchu(number)"]
        dic = get_www_getchu(number)
    else:
        dic = get_dl_getchu(number)

    if dic == None:
        return {"title" : ""}
    outline = ''
    _list = dic['outline']
    for i in _list:
        outline = outline + i
    dic['outline'] = outline

    result = json.dumps(dic,ensure_ascii=False, sort_keys=True, indent=4,separators=(',', ':'), )
    return result

if __name__ == '__main__':
    test = []
    for i in test:
        print(i)
        print(main(i))
