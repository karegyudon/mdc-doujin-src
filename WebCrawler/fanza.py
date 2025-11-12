import sys
sys.path.append('../')
from urllib.parse import urlencode
import time
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import os

def get_html_from_browserless(url, max_retries=3, timeout=70):
    """
    使用Selenium WebDriver从指定URL获取HTML内容
    
    参数:
        url: 要获取的网页URL
        max_retries: 最大重试次数
        timeout: 请求超时时间（秒）
        
    返回:
        获取到的HTML内容字符串，如果失败则返回空字符串
    """
    retry_count = 0
    last_error = None
    
    # 获取browserless配置
    try:
        # 尝试使用绝对导入
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import getInstance
            config = getInstance()
            browserless_url = config.puppeteer_url() if config and hasattr(config, 'puppeteer_url') else None
        except:
            # 如果绝对导入失败，回退到默认值
            browserless_url = None
            
        # 如果配置不存在或无效，使用默认值
        if not browserless_url:
            browserless_url = "http://10.10.32.153:3000/webdriver"
        
        # print(f"[+]DEBUG-webdriver: 配置的WebDriver服务地址: {browserless_url}")
    except Exception as e:
        print(f"[-]DEBUG-webdriver: 获取配置失败: {str(e)}")
        browserless_url = "http://10.10.32.153:3000/webdriver"
    
    # 重试逻辑
    while retry_count < max_retries:
        driver = None
        try:
            print(f"[+]DEBUG-webdriver: 获取URL内容: {url} (尝试 {retry_count + 1}/{max_retries})")
            
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--proxy-server={config.puppeteer_proxy()}')
            
            # 初始化WebDriver
            driver = webdriver.Remote(
                command_executor=browserless_url,
                options=chrome_options
            )

            # 访问URL
            driver.get(url)
            
            # 等待页面加载完成
            # time.sleep(3)
            
            # 获取页面内容
            final_html = driver.page_source
            
            # 验证内容有效性
            # if not final_html or len(final_html.strip()) < 100:
            #     print(f"[-]DEBUG-webdriver: 获取到的HTML内容过短或为空")
            #     retry_count += 1
            #     last_error = "Empty or invalid HTML content"
            #     time.sleep(2)
            #     continue
            
            # 写入调试文件
            debug_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webdriver_debug.html")
            try:
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(final_html)
                # print(f"[+]DEBUG-webdriver: 页面内容已保存到: {debug_file}")
            except Exception as write_error:
                # 处理写入调试文件失败的情况
                pass
            
            # print(f"[+]DEBUG-webdriver: 成功获取URL内容，长度: {len(final_html)} 字符")
            return final_html
            
        except Exception as e:
            error_msg = f"获取HTML内容异常: {str(e)}"
            print(f"[-]DEBUG-webdriver: {error_msg}")
            last_error = error_msg
            retry_count += 1
            time.sleep(2)
        finally:
            # 确保关闭driver
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
    # 所有重试都失败
    print(f"[-]DEBUG-webdriver: 所有重试都失败，最后错误: {last_error}")
    return ""

import json

from ADC_function import *
from WebCrawler.crawler import *
import config

class fanzaCrawler(Crawler):
    def getFanzaString(self,string):
        try:
            # 检查self.html是否存在且有xpath方法
            if not hasattr(self, 'html') or self.html is None or not hasattr(self.html, 'xpath'):
                return ""
            
            result1 = ""
            result2 = ""
            try:
                xpath_result = self.html.xpath("//td[contains(text(),'"+string+"')]/following-sibling::td/a/text()")
                if xpath_result:
                    result1 = str(xpath_result).strip(" ['']")
            except:
                pass
                
            try:
                xpath_result = self.html.xpath("//td[contains(text(),'"+string+"')]/following-sibling::td/text()")
                if xpath_result:
                    result2 = str(xpath_result).strip(" ['']")
            except:
                pass
                
            return result1+result2
        except Exception as e:
            print(f"[-]Error in getFanzaString for '{string}': {e}")
            return ""

    def getFanzaStrings(self, string):
        try:
            # 检查self.html是否存在且有xpath方法
            if not hasattr(self, 'html') or self.html is None or not hasattr(self.html, 'xpath'):
                return []
            
            try:
                result1 = self.html.xpath("//td[contains(text(),'" + string + "')]/following-sibling::td/a/text()")
                if isinstance(result1, list) and len(result1) > 0:
                    return result1
            except:
                pass
                
            try:
                result2 = self.html.xpath("//td[contains(text(),'" + string + "')]/following-sibling::td/text()")
                return result2 if isinstance(result2, list) else []
            except:
                return []
        except Exception as e:
            print(f"[-]Error in getFanzaStrings for '{string}': {e}")
            return []

    def getMetadata(self, property_name):
        """
        获取指定meta标签的content属性内容
        :param property_name: meta标签的property属性值，例如"og:title"
        :return: 对应的content属性内容
        """
        try:
            # 检查self.html是否存在且有xpath方法
            if not hasattr(self, 'html') or self.html is None or not hasattr(self.html, 'xpath'):
                print(f"[-]Error: Invalid html object when getting metadata for {property_name}")
                return ""
            
            result = self.html.xpath("//meta[@property='" + property_name + "']/@content")
            if result:
                return result[0].strip() if isinstance(result[0], str) else ""
            else:
                # 尝试使用name属性查找meta标签
                result_name = self.html.xpath("//meta[@name='" + property_name + "']/@content")
                if result_name:
                    return result_name[0].strip() if isinstance(result_name[0], str) else ""
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
            # 检查self.html是否存在且有xpath方法
            if not hasattr(self, 'html') or self.html is None or not hasattr(self.html, 'xpath'):
                return ""
            
            # 尝试多种可能的选择器
            selectors = [
                "//div[@class='circleName']//a/text()",
                "//div[contains(@class, 'circleName')]//a/text()",
                "//td[contains(text(),'メーカー：')]/following-sibling::td/a/text()",
                "//td[contains(text(),'メーカー：')]/following-sibling::td/text()"
            ]
            
            for selector in selectors:
                try:
                    studio_elements = self.html.xpath(selector)
                    if studio_elements and isinstance(studio_elements[0], str):
                        return studio_elements[0].strip()
                except:
                    continue
            
            return ""
        except Exception as e:
            print(f"[-]Error in getStudio: {e}")
            return ""


def getRelease(html):
    """
    从HTML源码中提取发布日期
    :param html: HTML源码字符串
    :return: 格式化后的日期字符串，如'2023-01-01'
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # 要搜索的关键词
        keywords = ['配信開始日', '発売日']
        
        # 遍历关键词，寻找匹配的内容
        for keyword in keywords:
            # 查找包含关键词的元素
            elements = soup.find_all(string=lambda text: text and keyword in text)
            
            for element in elements:
                # 获取包含该文本的父元素
                parent = element.find_parent()
                if parent:
                    # 查找下一个具有informationList__txt类的兄弟元素
                    next_info = parent.find_next(class_='informationList__txt')
                    if next_info:
                        # 获取文本内容并处理
                        date_text = next_info.get_text().strip()
                        
                        # 去掉时间部分，只保留日期（假设格式为"2014/04/25 10:00"）
                        if date_text:
                            # 按空格分割，取第一部分作为日期
                            date_part = date_text.split()[0] if ' ' in date_text else date_text
                            
                            # 格式化为标准格式（将/替换为-）
                            formatted_date = date_part.replace('/', '-')
                            return formatted_date
        
        # 如果上述方法都失败，尝试使用原始方法作为后备
        import re
        # 使用正则表达式搜索日期格式
        date_patterns = [
            r'(\d{4}/\d{2}/\d{2})',  # 2014/04/25格式
            r'(\d{4}-\d{2}-\d{2})'   # 2014-04-25格式
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1).replace('/', '-')
                
    except Exception as e:
        print(f"[-]Error in getRelease: {e}")
    
    # 如果无法提取日期，返回空字符串
    return ''

def getYear(release):
    """
    从release字符串中提取年份数字
    :param release: 格式如'2023-01-01'或'2023/01/01'的日期字符串
    :return: 年份数字字符串，如'2023'
    """
    try:
        import re
        # 使用正则表达式匹配年份（4位数字）
        year_match = re.search(r'(\d{4})', release)
        if year_match:
            return year_match.group(1)
        
        # 如果没有找到4位数字，尝试按分隔符拆分
        if '-' in release or '/' in release:
            parts = release.replace('/', '-').split('-')
            if parts and len(parts[0]) == 4 and parts[0].isdigit():
                return parts[0]
    except Exception as e:
        print(f"[-]Error in getYear: {e}")
    
    # 如果无法提取年份，返回空字符串
    return ''

def getTags(html):
    """
    从HTML源码中提取标签列表
    :param html: HTML源码字符串
    :return: 标签文本数组
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找<ul class="genreTagList">标签
        genre_tag_list = soup.find('ul', class_='genreTagList')
        
        if genre_tag_list:
            # 获取所有<div class="genreTag__item">标签
            tag_items = genre_tag_list.find_all('div', class_='genreTag__item')
            
            # 提取每个标签的文本内容
            tags = []
            for item in tag_items:
                tag_text = item.get_text().strip()
                if tag_text:  # 确保标签不为空
                    tags.append(tag_text)
            
            return tags
    except Exception as e:
        print(f"[-]Error in getTags: {e}")
    
    # 如果无法提取标签，返回空数组
    return []

def getSeries(html):
    """
    从HTML源码中提取系列信息
    :param html: HTML源码字符串
    :return: 系列名称字符串
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找dt标签，class为informationList__ttl，文本内容包含'シリーズ'
        series_dt = soup.find('dt', {'class': 'informationList__ttl', 'string': 'シリーズ'})
        
        # 如果直接查找失败，尝试更通用的方法
        if not series_dt:
            series_dts = soup.find_all('dt', class_='informationList__ttl')
            for dt in series_dts:
                if dt.string and 'シリーズ' in dt.string:
                    series_dt = dt
                    break
        
        if series_dt:
            # 获取dt标签后的第一个informationList__txt标签
            series_txt = series_dt.find_next(class_='informationList__txt')
            if series_txt:
                series_text = series_txt.get_text().strip()
                # 如果内容是'----'，返回空字符串
                if series_text == '----':
                    return ''
                return series_text
    except Exception as e:
        print(f"[-]Error in getSeries: {e}")
    
    # 如果无法提取系列信息，返回空字符串
    return ''


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
        # 首先尝试获取<p class="summary__txt">下的文本内容
        # 使用BeautifulSoup来处理br标签的替换
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(etree.tostring(html), 'html.parser')
        summary_tag = soup.find('p', class_='summary__txt')
        if summary_tag:
            # 替换所有br标签为/n
            for br in summary_tag.find_all('br'):
                br.replace_with('\n')

            result = summary_tag.get_text(separator='', strip=True).replace('<br>', '\n').replace('</br>', '\n')
            return result
        
        # 如果没有找到summary__txt类，则尝试原来的方法
        try:
            result = str(html.xpath("//div[@class='mg-b20 lh4']/text()")[0]).replace("\n", "")
            if result == "":
                result = str(html.xpath("//div[@class='mg-b20 lh4']//p/text()")[0]).replace("\n", "")
            return result
        except:
            pass
    except Exception as e:
        print(f"[-]Error in getOutline: {e}")
        # 静默失败，保持原有行为
    # 如果所有方法都失败，返回空字符串
    return ""


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

# 注意: 统一使用文件顶部定义的get_html_from_browserless函数

def main(number):
    """
    主函数，用于从fanza网站获取指定编号的内容信息
    
    参数:
        number: 要查询的编号
    
    返回:
        包含内容信息的JSON字符串
    """
    try:
        # 使用统一的browserless函数获取网页内容
        target_url = "https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number.lower() + "/"
        # print(f"[+]DEBUG-fanza: Target URL: {target_url}")
        
        bypass_url = "https://www.dmm.co.jp/age_check/=/declared=yes/?" + urlencode({'rurl': target_url})
        # print(f"[+]DEBUG-fanza: Fetching URL with browserless: {bypass_url}")
        
        htmlcode = get_html_from_browserless(bypass_url)
            
        # 初始化爬虫类
        fanza_Crawler = fanzaCrawler(htmlcode)
            
        # 尝试提取标题
        title = ""
        try:
            title = fanza_Crawler.getMetadata('og:title').strip()
            # print(f"[+]DEBUG-fanza: Extracted title: {title}")
        except Exception as e:
            print(f"[-]Error extracting title: {e}")
    
        # 解析htmlcode以获取数据
        # print("[+]DEBUG-fanza-html: parse begin")
        
        # 检查htmlcode是否有效
        if not htmlcode or not isinstance(htmlcode, str):
            print("[-]DEBUG-fanza: Invalid HTML content")
            data = {"title": "", "website": "https://www.dmm.co.jp", "source": "fanza"}
        else:
            try:
                # DEBUG: 将html内容写入debug.html文件    
                html = etree.fromstring(htmlcode, etree.HTMLParser())

                # 安全地获取metadata
                def safe_get_metadata(meta_name):
                    try:
                        value = fanza_Crawler.getMetadata(meta_name)
                        return value.strip() if value else ""
                    except:
                        return ""

                data = {
                    "title": title if title else safe_get_metadata('og:title'),
                    "studio": fanza_Crawler.getStudio(),
                    "outline": getOutline(html),
                    "runtime": '',
                    "director": '',
                    "actor": '',
                    "release": getRelease(htmlcode),
                    "number": number,
                    "cover": safe_get_metadata('og:image'),
                    "imagecut": 1,
                    "tag": getTags(htmlcode),
                    "extrafanart": '',
                    "label": '',
                    "year": getYear(getRelease(htmlcode)),
                    "actor_photo": '',
                    "website": "https://www.dmm.co.jp/dc/doujin/-/detail/=/cid=" + number,
                    "source": "fanza.py",
                    "series": getSeries(htmlcode),
                }
            except Exception as e:
                print(f"[-]Error parsing HTML content: {str(e)}")
                data = {
                    "title": "",
                    "website": "https://www.dmm.co.jp",
                    "source": "fanza"
                }
    
        js = json.dumps(
            data, ensure_ascii=False, sort_keys=True, indent=4, separators=(",", ":")
        )  # .encode('UTF-8')
        return js
        
    except Exception as e:
        print(f"[-]Error in main function: {str(e)}")
        data = {
            "title": "",
            "website": "https://www.dmm.co.jp",
            "source": "fanza"
        }
        return json.dumps(data, ensure_ascii=False)
    except:
        # 捕获所有其他未预期的异常
        print("[-]Unexpected error in main function")
        data = {
            "title": "",
            "website": "https://www.dmm.co.jp",
            "source": "fanza"
        }
        return json.dumps(data, ensure_ascii=False)

if __name__ == "__main__":
    print(main("d_sm0002"))
