import re
from lxml import etree
import json
import sys
import operator
import datetime
sys.path.append('../')
from ADC_function import *

def getTitle(html):
    result = str(html.xpath('/html/head/title/text()')[0])
    result = result[:result.rfind(' | DLsite')]
    result = result[:result.rfind(' [')]
    if operator.contains(result, 'OFF】'):
        result = result[result.find('】')+1:]
    result = result.replace('【HD版】', '')
    # print("[+]DEBUG-getTitle:", result)
    return result
def getActor(html):  # //*[@id="center_column"]/div[2]/div[1]/div/table/tbody/tr[1]/td/text()
    try:
        # 查找<th>声优</th>下的所有<a>标签中的文本内容
        actors = html.xpath('//th[contains(text(),"声优")]/../td/a/text()')
        # 直接返回获取到的声优列表
        if actors:
            result = actors
        else:
            result = []
    except:
        result = []
    # print("[+]DEBUG-getActor:", result)
    return result
def getActorPhoto(actor): #//*[@id="star_qdt"]/li/a/img
    try:
        a = actor.split(',')
        d={}
        for i in a:
            p={i:''}
            d.update(p)
        return d
    except:
        return ''
def getStudio(html):
    try:
        # 查找<span itemprop="brand" class="maker_name">标签下第一个<a>标签所包含的文本
        result = html.xpath('//span[@itemprop="brand" and @class="maker_name"]/a/text()')[0]
        if not result:
           result = html.xpath('//span[@itemprop="brand" and @class="work_maker"]/a/text()')[0]
    except:
        # 如果找不到就返回空值
        result = ''
    # print("[+]DEBUG-getStudio:", result)
    return result
def getRuntime(html):
    try:
        # 查找包含"収録時間："的文本节点
        text_nodes = html.xpath('//text()')
        for text in text_nodes:
            if "収録時間：" in text:
                # 提取"収録時間："后的内容
                result = text.split("収録時間：", 1)[1].strip().replace('分', '')
                # print("[+]DEBUG-getRuntime:", result)
                return result
        # 如果没有找到"収録時間："，返回空值
        return ''
    except:
        return ''
def getLabel(html):
    try:
        try:
            result = html.xpath('//th[contains(text(),"系列名")]/../td/span[1]/a/text()')[0]
        except:
            result = html.xpath('//th[contains(text(),"社团名")]/../td/span[1]/a/text()')[0]
    except:
        result = ''
    return result
def getYear(html):
    try:
        # 获取getRelease函数的输出结果
        release_result = getRelease(html)
        # 如果结果不为空，提取前4位数字作为年份
        if release_result:
            # 使用正则表达式提取前4位数字
            year_match = re.search(r'\d{4}', release_result)
            if year_match:
                result = year_match.group()
            else:
                # 如果无法提取4位数字，则使用当前年份
                result = str(datetime.datetime.now().year)
        else:
            # 如果结果为空，则使用当前年份
            result = str(datetime.datetime.now().year)
        # print("[+]DEBUG-getYear:", result)
        return result
    except:
        # 异常情况下返回当前年份
        return str(datetime.datetime.now().year)
def getRelease(html):
    try:
        # 搜索包含"发售日"或"贩卖日"的th标签，然后提取td下a标签的文本内容
        result = ''
        # 首先尝试查找"贩卖日"
        sell_date = html.xpath('//th[contains(text(),"贩卖日")]/../td/a/text()')
        if sell_date:
            result = sell_date[0]
        # 如果没有找到"贩卖日"，则尝试查找"发售日"
        if not result:
            release_date = html.xpath('//th[contains(text(),"发售日")]/../td/a/text()')
            if release_date:
                result = release_date[0]
        # 将日期格式从"2025年06月27日"调整为"2025-06-27"
        if result:
            result = result.replace('年','-').replace('月','-').replace('日','')
        # print("[+]DEBUG-getRelease:", result)
        return result
    except:
        return ''

def getTag(html):
    try:
        # 更准确地获取标签信息，排除"文件容量"等非标签信息
        result = []
        
        # 获取所有的<div class="main_genre">元素
        all_genre_divs = html.xpath('//div[@class="main_genre"]')
        
        # 定义需要跳过的th标签关键词
        skip_keywords = ["文件容量"]
        
        for div in all_genre_divs:
            # 查找这个div的祖先元素中的th标签
            ancestor_th = div.xpath('./ancestor::tr/th')
            
            # 检查是否应该跳过这个div
            should_skip = False
            if ancestor_th:
                # 获取th标签的文本内容
                th_text_nodes = ancestor_th[0].xpath('.//text()')
                if th_text_nodes:
                    th_text = ''.join(th_text_nodes).strip()
                    # 检查th文本是否包含跳过关键词
                    for keyword in skip_keywords:
                        if keyword in th_text:
                            should_skip = True
                            break
            
            # 如果不应该跳过，则获取这个div的文本内容
            if not should_skip:
                texts = div.xpath('.//text()')
                texts = [text.strip() for text in texts if text.strip()]
                result.extend(texts)
        
        # print("[+]DEBUG-getTag:", result)
        return result
    except:
        return []

def getCover_small(a, index=0):
    # same issue mentioned below,
    # javdb sometime returns multiple results
    # DO NOT just get the firt one, get the one with correct index number
    html = etree.fromstring(a, etree.HTMLParser())  # //table/tr[1]/td[1]/text()
    try:
        # 首先尝试从meta标签的og:image属性提取
        result = html.xpath('//meta[@property="og:image"]/@content')[0]
        # print("[+]DEBUG-getCover_small:", result.replace('.webp', '.jpg'))
        return result.replace('.webp', '.jpg')
    except:
        try:
            result = html.xpath("//div[@class='item-image fix-scale-cover']/img/@src")[index]
            # print("[+]DEBUG-getCover_small:", result.replace('.webp', '.jpg'))
            return result.replace('.webp', '.jpg')
        except: # 2020.7.17 Repair Cover Url crawl
            result = html.xpath("//div[@class='item-image fix-scale-cover']/img/@data-src")[index]
            if result.startswith('//'):
                result = 'https:' + result
            # print("[+]DEBUG-getCover_small:", result.replace('.webp', '.jpg'))
            return result.replace('.webp', '.jpg')
def getCover(html):
    try:
        # 首先尝试从meta标签的og:image属性提取
        result = html.xpath('//meta[@property="og:image"]/@content')[0]
        # print("[+]DEBUG-getCover:", result.replace('.webp', '.jpg'))
        return result.replace('.webp', '.jpg')
    except:
        try:
            # 如果第一种方式失败，尝试原来的XPath提取方式
            result = html.xpath('//*[@id="work_left"]/div/div/div[2]/div/div[1]/div[1]/ul/li[1]/picture/source/@srcset')[0]
            # print("[+]DEBUG-getCover:", result.replace('.webp', '.jpg'))
            return result.replace('.webp', '.jpg')
        except:
            try:
                # 如果第二种方式失败，尝试备用XPath提取meta标签的content属性
                result = html.xpath('//meta[@itemprop="image"]/@content')[0]
                return result
            except:
                # 如果所有方式都失败，返回空字符串
                return ''
def getDirector(html):
    try:
        # 查找<th>剧情</th>下的所有<a>标签中的文本内容
        directors = html.xpath('//th[contains(text(),"剧情")]/../td/a/text()')[0]
        # 直接返回获取到的导演列表作为字符串数组
        if directors:
            result = directors
        else:
            result = ''
    except:
        result = ''
    # print("[+]DEBUG-getDirector:", result)
    return result
def getOutline(html):
    try:
        total = []
        result = html.xpath('//*[@class="work_parts_area"]/p/text()')
        #result = html.xpath('//div[@class="work_parts type_text"]')
        for i in result:
            total.append(i.strip('\r\n'))
        result = str(total).strip(" ['']").replace("', '', '", r'\n').replace("', '", r'\n').replace("\\u3000", r' ').strip(", '', '")
        # print("[+]DEBUG-getOutline:", result)
        return result
    except:
        return ''
def getSeries(html):
    try:
        # 查找<th>系列名</th>下的<a>标签中的文本内容
        result = html.xpath('//th[contains(text(),"系列名")]/../td/a/text()')[0]
    except:
        # 如果找不到"系列名"，则尝试原来的查找方式
        try:
            result = html.xpath('//th[contains(text(),"社团名")]/../td/span[1]/a/text()')[0]
        except:
            result = ''
    # print("[+]DEBUG-getSeries:", result)
    return result
#
def getExtrafanart(html):
    try:
        result = []
        for i in html.xpath('//*[@id="work_left"]/div/div/div[1]/div/@data-src'):
            result.append("https:" + i)
    except:
        result = ''
    # print("[+]DEBUG-getExtrafanart:", result)
    return result
def main(number):
    try:
        if "RJ" in number or "VJ" in number:
            number = number.upper()
            target_url = 'https://www.dlsite.com/maniax/work/=/product_id/' + number + '.html/?locale=zh_CN'
            print("[+]DEBUG:", str(target_url))
            htmlcode = get_html(target_url, cookies={'locale': 'zh-cn'}, encoding='utf-8')
            # DEBUG: 将html内容写入debug.html文件
            with open('debug.html', 'w', encoding='utf-8') as f:
               f.write(htmlcode)
            html = etree.fromstring(htmlcode, etree.HTMLParser())
        else:
            htmlcode = get_html(f'https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category/male/keyword/{number}/order/trend/work_type_category/movie', cookies={'locale': 'zh-cn'})
            html = etree.HTML(htmlcode)
            search_result = html.xpath('//*[@id="search_result_img_box"]/li[1]/dl/dd[2]/div[2]/a/@href')
            if len(search_result) == 0:
                number = number.replace("THE ANIMATION", "").replace("he Animation", "").replace("t", "").replace("T","")
                html = etree.HTML(get_html(
                    f'https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category/male/keyword/{number}/order/trend/work_type_category/movie', cookies={'locale': 'zh-cn'}))
                search_result = html.xpath('//*[@id="search_result_img_box"]/li[1]/dl/dd[2]/div[2]/a/@href')
                if len(search_result) == 0:
                    if "～" in number:
                        number = number.replace("～","〜")
                    elif "〜" in number:
                        number = number.replace("〜","～")
                    html = etree.HTML(get_html(
                        f'https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category/male/keyword/{number}/order/trend/work_type_category/movie', cookies={'locale': 'zh-cn'}))
                    search_result = html.xpath('//*[@id="search_result_img_box"]/li[1]/dl/dd[2]/div[2]/a/@href')
                    if len(search_result) == 0:
                        number = number.replace('上巻', '').replace('下巻', '').replace('前編', '').replace('後編', '')
                        html = etree.HTML(get_html(
                            f'https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category/male/keyword/{number}/order/trend/work_type_category/movie', cookies={'locale': 'zh-cn'}))
                        search_result = html.xpath('//*[@id="search_result_img_box"]/li[1]/dl/dd[2]/div[2]/a/@href')
            a = search_result[0]
            html = etree.HTML(get_html(a,cookies={'locale': 'zh-cn'}))
            number = str(re.findall(r"\wJ\w+",a)).strip(" [']")
        dic = {
            'actor': getActor(html),
            'title': getTitle(html),
            'studio': getStudio(html),
            'outline': getOutline(html),
            'runtime': getRuntime(html),
            'director': getDirector(html),
            'release': getRelease(html),
            'number': number,
            'cover': getCover(html),
            'cover_small': '',
            'imagecut': 4,
            'tag': getTag(html),
            'label': getSeries(html),
            'year': getYear(html),  # str(re.search('\d{4}',getRelease(a)).group()),
            'actor_photo': '',
            'website': 'https://www.dlsite.com/maniax/work/=/product_id/' + number + '.html',
            'source': 'dlsite.py',
            'series': getSeries(html),
            'extrafanart':getExtrafanart(html),
            'allow_number_change':True,
        }
        js = json.dumps(dic, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'), )  # .encode('UTF-8')
        return js
    except Exception as e:
        if config.getInstance().debug():
            print(e)
        data = {
            "title": "",
        }
        js = json.dumps(
            data, ensure_ascii=False, sort_keys=True, indent=4, separators=(",", ":")
        )
        return js

#main('RJ061178')
#input("[+][+]Press enter key exit, you can check the error messge before you exit.\n[+][+]按回车键结束，你可以在结束之前查看和错误信息。")

if __name__ == "__main__":
    config.getInstance().set_override("debug_mode:switch=1")
    print(main('牝教師4～穢された教壇～ 「生意気ドジっ娘女教師・美結～高飛車ハメ堕ち2濁金」'))
    print(main('RJ329607'))