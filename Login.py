from requests import session

class AutoLogin:
    def __init__(self):
        # 登录信息
        self.login_cookies = {}
        self.web_cookies = {}
        self.session = session()
        self.login_id: str = '123'  # 大麦网登录账户名
        self.login_password: str = '123'  # 大麦网登录密码
        # 静态参数
        self.login_cookies_pkl = 'cookies.pkl'
        self.web_cookies_pkl = 'cookies_web.pkl'

