#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
from urllib.parse import urlencode

from ADC_function import *
from WebCrawler.crawler import *

class fanzaCrawler(Crawler):
    def getFanzaString(self,string):
        result1 = str(self.html.xpath("//td[contains(text(),'"+string+"')]/following-sibling::td/a/text()")).strip(" ['']")
        result2 = str(self.html.xpath("//td[contains(text(),'"+string+"')]/following-sibling::td/text()")).strip(" ['']")
        return result1+result2

    def getFanzaStrings(self, string):
        result1 = self.html.xpath("//td[contains(text(),'" + string + "')]/following-sibling::td/a/text()")
        if len(result1) > 0:
            return result1
        result2 = self.html.xpath("//td[contains(text(),'" + string + "')]/following-sibling::td/text()")
        return result2

    def getMetadata(self, property_name):
        """
        获取指定meta标签的content属性内容
        :param property_name: meta标签的property属性值，例如"og:title"
        :return: 对应的content属性内容
        """
        try:
            result = self.html.xpath("//meta[@property='" + property_name + "']/@content")
            if result:
                return result[0].strip()
            else:
                return ""
        except Exception as e:
            print(f"[-]Error getting metadata for property {property_name}: {e}")
            return ""

    def getStudio(self):
        """
        从<div class="circleName">下获取第一个<a>标签的文本作为Studio
        :return: Studio名称或空字符串
        """
        try:
            studio_elements = self.html.xpath("//div[@class='circleName']//a/text()")
            if studio_elements:
                return studio_elements[0].strip()
            else:
                return ""
        except:
            return ""


def getRelease(fanza_Crawler):
    result = fanza_Crawler.getFanzaString('発売日：')
    if result == '' or result == '----':
        result = fanza_Crawler.getFanzaString('配信開始日：')
    return result.replace("/", "-").strip('\\n')


def getCover(html, number):
    cover_number = number
    try:
        result = html.xpath('//*[@id="' + cover_number + '"]/@href')[0]
    except:
        # sometimes fanza modify _ to \u0005f for image id
        if "_" in cover_number:
            cover_number = cover_number.replace("_", r"\u005f")
        try:
            result = html.xpath('//*[@id="' + cover_number + '"]/@href')[0]
        except:
            # (TODO) handle more edge case
            # print(html)
            # raise exception here, same behavior as before
            # people's major requirement is fetching the picture
            raise ValueError("can not find image")
    return result


def getOutline(html):
    try:
        result = str(html.xpath("//div[@class='mg-b20 lh4']/text()")[0]).replace("\n", "")
        if result == "":
            result = str(html.xpath("//div[@class='mg-b20 lh4']//p/text()")[0]).replace("\n", "")
    except:
        # (TODO) handle more edge case
        # print(html)
        return ""
    return result


def getExtrafanart(htmlcode):  # 获取剧照
    html_pather = re.compile(r'<div id=\"sample-image-block\"[\s\S]*?<br></div>\n</div>')
    html = html_pather.search(htmlcode)
    if html:
        html = html.group()
        extrafanart_pather = re.compile(r'<img.*?src=\"(.*?)\"')
        extrafanart_imgs = extrafanart_pather.findall(html)
        if extrafanart_imgs:
            s = []
            for img_url in extrafanart_imgs:
                img_urls = img_url.rsplit('-', 1)
                img_url = img_urls[0] + 'jp-' + img_urls[1]
                s.append(img_url)
            return s
    return ''

def main(number):
    # fanza allow letter + number + underscore, normalize the input here
    # @note: I only find the usage of underscore as h_test123456789
    # print("[+]DEBUG-fanza:", number)
    
    htmlcode = ""
    cookies = {}
    title = ""
    
    # 检查是否存在cookie文件，如果存在则优先使用
    if os.path.exists('fanza_cookie.txt'):
        try:
            with open('fanza_cookie.txt', 'r') as f:
                cookies_str = f.read()
                if cookies_str:
                    import ast
                    cookies = ast.literal_eval(cookies_str)
        except Exception as e:
            print(f"[-]Error reading cookies: {e}")
            cookies = {}
    
    # 使用现有cookie尝试访问
    htmlcode = get_html("https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number.lower() + "/", cookies=cookies)
    
    # 检查是否能正确获取到title
    fanza_Crawler = fanzaCrawler(htmlcode)
    try:
        title = fanza_Crawler.getMetadata('og:title').strip()
    except:
        title = ""
    
    # 如果title为空，说明需要重新获取cookie
    if not title:
        print("[+]DEBUG-fanza: title is empty, need to re-fetch cookies")
        # 创建一个会话对象来处理cookie
        import requests
        session = requests.Session()
        
        # 第一次访问获取cookie
        target_url = "https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number.lower() + "/"
        try:
            response = session.get(target_url)
            # DEBUG: 将html内容写入f1.html文件
            with open('f1.html', 'w', encoding='utf-8') as f:
               f.write(response.text)

            # 保存cookie到文件
            with open('fanza_cookie.txt', 'w') as f:
                f.write(str(session.cookies.get_dict()))
            cookies = session.cookies.get_dict()
        except Exception as e:
            print(f"[-]Error getting initial cookies: {e}")
        
        # 第二次访问使用保存的cookie
        encoded_url = urlencode("https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number.lower() + "/")
        agecheckbypassurl = "https://www.dmm.co.jp/age_check/=/declared=yes/?rurl={}".format(encoded_url)
        print("[+]DEBUG-fanza-html:", agecheckbypassurl)
        
        # 使用cookie进行第二次访问
        htmlcode = get_html(agecheckbypassurl, cookies=cookies)
        # DEBUG: 将html内容写入f2.html文件
        with open('f2.html', 'w', encoding='utf-8') as f:
               f.write(htmlcode)

        # 第三次访问获取最终页面
        htmlcode = get_html("https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number.lower() + "/", cookies=cookies)
        
        # DEBUG: 将html内容写入f3.html文件
        with open('f3.html', 'w', encoding='utf-8') as f:
               f.write(htmlcode)
        
        # 重新解析htmlcode以获取最新的数据
        fanza_Crawler = fanzaCrawler(htmlcode)
        try:
            title = fanza_Crawler.getMetadata('og:title').strip()
        except:
            title = ""
        
        # 再次检查title是否获取成功
        if not title:
            print("[+]DEBUG-fanza: title is still empty after re-fetching cookies")
    
    # 解析htmlcode以获取数据
    try:
        print("[+]DEBUG-fanza-html: parse begin")
        # DEBUG: 将html内容写入debug.html文件    
        html = etree.fromstring(htmlcode, etree.HTMLParser())

        data = {
            "title": title if title else fanza_Crawler.getMetadata('og:title').strip(),
            "studio": fanza_Crawler.getStudio(),
            "outline": '',
            "runtime": '',
            "director": '',
            "actor": '',
            "release": '',
            "number": number,
            "cover": fanza_Crawler.getMetadata('og:image').strip(),
            "imagecut": 1,
            "tag": '',
            "extrafanart": '',
            "label": '',
            "year": '',
            "actor_photo": '',
            "website": "https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number,
            "source": "fanza.py",
            "series": '',
        }
    except Exception as e:
        data = {
            "title": "",
        }
    js = json.dumps(
        data, ensure_ascii=False, sort_keys=True, indent=4, separators=(",", ":")
    )  # .encode('UTF-8')
    return js


# def main_htmlcode(number):
#     # fanza allow letter + number + underscore, normalize the input here
#     # @note: I only find the usage of underscore as h_test123456789
#     htmlcode = get_html("https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number)

#     # fanza_search_number = number
#     # # AV_Data_Capture.py.getNumber() over format the input, restore the h_ prefix
#     # if fanza_search_number.startswith("h-"):
#     #     fanza_search_number = fanza_search_number.replace("h-", "h_")

#     # # fanza_search_number = re.sub(r"[^0-9a-zA-Z_]", "", fanza_search_number).lower()

#     # fanza_urls = [
#     #     "https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=",
#     #     "https://www.dmm.co.jp/digital/anime/-/detail/=/cid=",
#     #     "https://www.dmm.co.jp/mono/anime/-/detail/=/cid=",
#     # ]
#     # chosen_url = ""
#     # for url in fanza_urls:
#     #     chosen_url = url + fanza_search_number
#     #     htmlcode = get_html(chosen_url)
#     #     if "404 Not Found" not in htmlcode:
#     #         break
#     # if "404 Not Found" in htmlcode:
#     #     return json.dumps({"title": "",})
#     return htmlcode

if __name__ == "__main__":
    # print(main("DV-1562"))
    # print(main("96fad1217"))
    # print(main("AES-002"))
    # print(main("MIAA-391"))
    # print(main("OBA-326"))
    # 只保留一个测试调用，避免重复输出调试信息
    print(main("AES-002"))
