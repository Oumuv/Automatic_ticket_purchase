# -*- coding: UTF-8 -*-
"""
__Author__ = "MakiNaruto"
__Version__ = "2.1.0"
__Description__ = ""
__Created__ = 2022/2/14 10:37 下午
"""

import re
import os
import json
import platform
from telnetlib import EC
from time import sleep
from urllib.parse import urlencode
import requests
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from Login import AutoLogin
import tools
import argparse
from requests import session
from seleniumwire import webdriver

class DaMaiTicket:


    def __init__(self):
        # 登录信息
        self.login_cookies = {}
        self.web_cookies = {}
        self.session = session()
        # 以下为抢票必须的参数
        self.item_id: int = 707744544748  # 商品id
        self.perform_id = ''  # 场次id，不填则默认
        self.viewer: list = ['欧银锋','李雨宁']  # 在大麦网已填写的观影人
        self.buy_nums: int = 2  # 购买影票数量, 需与观影人数量一致
        self.ticket_price: int = 580  # 购买指定票价
        # 静态参数
        self.login_cookies_pkl = 'cookies.pkl'
        self.web_cookies_pkl = 'cookies_web.pkl'
        self.need_post_url = False


    def run(self):
        if len(self.viewer) != self.buy_nums:
            print('-' * 10, '购买数量与实际观演人数量不符', '-' * 10)
            return
        if os.path.exists(self.login_cookies_pkl):
            cookies = tools.load_cookies(self.login_cookies_pkl)
            self.login_cookies.update(cookies)
            self.web_cookies = tools.load_cookies(self.web_cookies_pkl)
        elif 'account' == args.mode.lower():
            login = AutoLogin()
            self.login_cookies, self.web_cookies = tools.account_login('account', login.login_id, login.login_password)
        else:
            self.login_cookies, self.web_cookies = tools.account_login('qr')

        login_status = tools.check_login_status(self.login_cookies)

        if not login_status:
            print('-' * 10, '登录失败, 请检查登录账号信息。若使用保存的cookies，则删除cookies文件重新尝试', '-' * 10)
            return
        elif login_status and not os.path.exists(self.login_cookies_pkl):
            tools.save_cookies(self.login_cookies, self.login_cookies_pkl)
            tools.save_cookies(self.web_cookies, self.web_cookies_pkl)

        # 构建api参数
        commodity_param, ex_params = tools.get_api_param()
        if len(self.perform_id) > 0:
            # 选择指定场次
            commodity_param.update({"dataType": 2, "dataId": self.perform_id})

        while True:
            # 获取spu、sku参数
            ticket_info, sku_id_sequence, sku_id = self.getGoodsInfo(self.item_id, commodity_param,
                                                                             ticket_price=self.ticket_price)
            if len(sku_id) == 0:
                print("SKU不存在，请检查参数是否正确：【self.ticket_price】")
                return

            # 获取当前时间
            now = datetime.now()
            # 将当前时间格式化为 "202305181100" 格式
            formatted_time = now.strftime("%Y%m%d%H%M")
            start_time = ticket_info['itemBasicInfo']['sellingStartTime']
            if int(formatted_time) < int(start_time):
                print('-' * 10, '当前时间：', now.strftime("%Y%m%d%H%M%S"), '开始时间: ', start_time, '-' * 10)
                sleep(1)
                continue

            ticket_sku_status = ticket_info['skuPagePcBuyBtn']['skuBtnList'][sku_id_sequence]['btnText']
            if ticket_sku_status == '缺货登记':
                print('-' * 10, '手慢了，该票价已经售空: ', ticket_sku_status, '-' * 10)
                sleep(1)
                continue
            elif ticket_sku_status == '立即购买':
                break
            elif ticket_sku_status == '立即预订':
                break
            elif ticket_sku_status == '该渠道不支持购买':
                break
            else:
                print('-' * 10, '当前状态: ', ticket_sku_status, '-' * 10)
                sleep(1)
                continue

        # 构建页面URL参数：提交订单
        buy_serial_number = '{}_{}_{}'.format(self.item_id, self.buy_nums, sku_id)
        buy_pay_params = {
            'buyParam':buy_serial_number,
            'buyNow': 'true',
            'exParams': json.dumps(ex_params),
            'spm': 'a2o71.project.0.bottom'
        }
        url_pamras = urlencode(buy_pay_params)
        buy_pay_url = "https://m.damai.cn/app/dmfe/h5-ultron-buy/index.html?" + url_pamras

        # 创建driver
        driver = createChromeDriver()
        driver.get("https://m.damai.cn/damai/mine/audience/index.html")
        # 共享cookie
        for cookie in self.web_cookies:
            driver.add_cookie(cookie)
        # 执行抢票逻辑
        is_ok = False
        index = 0
        count = 1
        while not is_ok:
            is_ok, index, count = execute(self, driver, buy_pay_url, index, count)

        driver.refresh()



    def getGoodsInfo(self, item_id, commodity_param, ticket_price=None):
        """
        获取点击购买所必须的参数信息
        :param item_id:             商品id
        :param commodity_param:     获取商品购买信息必须的参数
        :param ticket_price:        购买指定价位的票
        :return:
        """
        if not ticket_price:
            print('-' * 10, '票价未填写, 请选择票价', '-' * 10)
            return False

        commodity_param.update({'itemId': item_id})
        headers = {
            'authority': 'detail.damai.cn',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': 'https://detail.damai.cn/item.htm',
            'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        }

        response = self.session.get('https://detail.damai.cn/subpage', headers=headers, params=commodity_param, verify=False)
        ticket_info = json.loads(response.text.replace('null(', '').replace('__jp0(', '')[:-1])
        all_ticket_sku = ticket_info['perform']['skuList']
        sku_id_sequence = 0
        sku_id = ''
        if ticket_price:
            for index, sku in enumerate(all_ticket_sku):
                if sku.get('price') and float(sku.get('price')) == float(ticket_price):
                    sku_id_sequence = index
                    sku_id = sku.get('skuId')
                    break
        return ticket_info, sku_id_sequence, sku_id


def createChromeDriver():
    option = webdriver.ChromeOptions()  # 默认Chrome浏览器
    # 关闭开发者模式, window.navigator.webdriver 控件检测到你是selenium进入，若关闭会导致出现滑块并无法进入。
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('--disable-blink-features=AutomationControlled')
    # option.add_argument('headless')               # Chrome以后台模式进行，注释以进行调试
    # option.add_argument('window-size=1920x1080')  # 指定分辨率
    # option.add_argument('no-sandbox')             # 取消沙盒模式
    # option.add_argument('--disable-gpu')          # 禁用GPU加速
    # option.add_argument('disable-dev-shm-usage')  # 大量渲染时候写入/tmp而非/dev/shm
    if platform.system().lower() == 'linux':
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_linux')
    elif platform.system().lower() == 'windows':
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_windows')
    else:
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_mac')

    driver = webdriver.Chrome(chromedriver, options=option)
    driver.set_page_load_timeout(60)
    driver.set_window_size(300, 800)
    return driver

def execute(self, driver, buy_pay_url, start_index, run_count):
    # 商品详情地址
    driver.get(buy_pay_url)
    try:
        # 是否出现防水墙
        WebDriverWait(driver, 3, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="baxia-dialog-content"]')))
        driver.switch_to.frame('baxia-dialog-content')
        print("订单确认页出现防水墙")
        # 定位到滑块按钮元素
        ele_button = driver.find_element(By.XPATH, '//*[@id="nc_1_n1z"]')
        # 打印滑块按钮的宽和高
        # print('滑块按钮的宽：', ele_button.size['width'])
        # print('滑块按钮的高：', ele_button.size['height'])
        # 定位到滑块区域元素
        ele = driver.find_element(By.XPATH, '//*[@id="nc_1__scale_text"]')
        # 打印滑块区域的宽和高
        print('滑块区域的宽：', ele.size['width'])
        print('滑块区域的高：', ele.size['height'])
        # 拖动滑块
        chains = ActionChains(driver)
        chains.click_and_hold(ele_button)
        count = ele.size['width'] / 5
        print('滑块单次拖动距离：', count)
        for i in range(5):
            chains.move_by_offset(count, 0).perform()  # perform 立即执行,共要拖动286px
            sleep(0.3)
        chains.release()
    except:
        print("正常访问订单确认页")

    driver.switch_to.default_content()
    # 出现提交订单按钮
    sm_btn = WebDriverWait(driver, 100, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dmOrderSubmitBlock_DmOrderSubmitBlock"]/div[2]/div/div[2]/div[3]/div[2]')))
    # 勾选观演人
    viewer_checkbox_list = driver.find_elements(By.XPATH, '//*[@id="dmViewerBlock_DmViewerBlock"]/div[2]/div/div')
    for d in viewer_checkbox_list:
        if re.split('\s+', d.text)[0] in self.viewer:
            d.click()
            print("选中观影人：" + re.split('\s+', d.text)[0])
    # 提交订单
    sm_btn.click()

    is_success = False
    # 睡眠一秒
    sleep(1)
    request_list = driver.requests
    create_order_request = []
    for i in range(start_index, len(request_list)):
        # 抓取提交订单请求
        # if '/h5/mtop.trade.order.build.h5/' in request_list[i].path:
        if '/h5/mtop.trade.order.create.h5/4.0/' in request_list[i].path:
            create_order_request.append(request_list[i])
            print(run_count, "|", start_index, "|", request_list[i])
            start_index = i

    if self.need_post_url:
        response_list = []
        if len(create_order_request) != 0 and self.need_post_url:
            send_request = create_order_request[0]
            for i in range(2):
                # 爆破提交订单接口2次（大麦做了接口防刷，同一个签名的接口只能调用1~2次）
                response = requests.post(send_request.url,
                                         data=send_request.params,
                                         headers=send_request.headers,
                                         cookies=self.login_cookies,
                                         verify=False)
                # 爆破成功

                # is_success = True
                response_list.append(response)
                print(str(run_count) + "|" + str(start_index) + "|" + response.text)

    run_count += 1
    if run_count > 500 or is_success:
        return True, start_index, run_count
    else:
        return False, start_index, run_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--mode', type=str, default='account', required=False,
                        help='account: account login， QR: Scan QR code login')
    args = parser.parse_args()
    a = DaMaiTicket()
    a.run()