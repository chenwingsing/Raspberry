import time
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from collections import defaultdict

# ===================== 配置区域 =====================
RSI_PERIOD = 6  # RSI计算周期
RSI_OVERBUY = 80  # 超买阈值
RSI_OVERSOLD = 20  # 超卖阈值
CHECK_INTERVAL = 3  # 检查间隔（分钟）
MAX_WORKERS = 6  # 最大并发线程数
BOLLINGER_WINDOW = 20  # 布林带计算窗口
BOLLINGER_STD = 2  # 布林带标准差倍数

ETF_LIST = [
    # 格式: (ETF名称, 代码)
    # 消费类
    ("主要消费ETF", "159928"),  # 深交所
    ("酒ETF", "512690"),  # 上交所
    ("细分食品饮料ETF", "515710"),  # 上交所

    # 医药类
    ("医疗ETF", "512170"),  # 上交所
    ("生物医药ETF", "512290"),  # 上交所

    # 科技类
    ("科技龙头ETF", "515000"),  # 上交所
    ("半导体芯片ETF", "159995"),  # 深交所
    ("人工智能ETF", "515980"),  # 上交所
    #("5G通信主题ETF", "515050"),  # 上交所
    ("计算机主题ETF", "512720"),  # 上交所

    # 新能源类
    ("新能源汽车ETF", "515030"),  # 上交所
    ("光伏产业ETF", "515790"),  # 上交所
    ("碳中和ETF", "159790"),  # 深交所

    # 周期类
    ("有色金属ETF", "512400"),  # 上交所
    ("煤炭ETF", "515220"),  # 上交所
    #("钢铁ETF", "515210"),  # 上交所
    #("化工ETF", "159870"),  # 深交所

    # 金融地产类
    ("银行ETF", "512800"),  # 上交所
    ("证券ETF", "512880"),  # 上交所
    ("房地产ETF", "512200"),  # 上交所

    # 宽基指数类
    ("沪深300ETF", "510300"),  # 上交所
    ("创业板50ETF", "159949"),  # 深交所

    # 其他主题类
    ("军工ETF", "512660"),  # 上交所
    ("黄金ETF", "518880"),  # 上交所
    ("农业主题ETF", "159825"),  # 深交所
    #("家电ETF", "159996"),  # 深交所
    #("传媒ETF", "512980"),  # 上交所
    ("畜牧养殖ETF", "159865"),  # 深交所
    ("基建ETF", "516950"),  # 上交所
    #("现代物流ETF", "516910"),  # 上交所
    ("稀土产业ETF", "516780"),  # 上交所
    ("旅游主题ETF", "159766"),  # 深交所
    ("电力ETF", "159611"),  # 深交所
    ("红利ETF", "510880"),  # 上交所
    ("纳斯达克ETF", "159632"),
    ("标普500ETF", "513650")

]

# 邮件配置
my_sender = 'xxx'  # 发件人QQ邮箱账号
my_pass = 'xxx'  # 发件SMTP授权码
my_user = 'xxx'  # 收件人QQ邮箱账号，自己发自己就行
# ===================================================

def mail(content):
    ret = True
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr(["A股RSI监控", my_sender])
        msg['To'] = formataddr(["A股RSI监控", my_user])
        msg['Subject'] = "A股RSI监控"

        msg.attach(MIMEText(content, 'plain', 'utf-8'))

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, [my_user, ], msg.as_string())
        server.quit()
    except Exception:
        ret = False
    return ret

def get_full_symbol(code):
    """智能补全交易所代码"""
    if code.startswith(('5', '6', '9')):
        return f"sh{code}"
    elif code.startswith(('0', '1', '2', '3')):
        return f"sz{code}"
    return code

def fetch_historical_data(etf_code):
    """获取历史数据"""
    try:
        df = ak.fund_etf_hist_em(symbol=etf_code, adjust="qfq")
        if df.empty:
            print(f"获取 {etf_code} 历史数据失败: 数据为空")
            return None
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values(by='日期', ascending=True)
        return df
    except Exception as e:
        print(f"获取 {etf_code} 历史数据失败: {e}")
    return None

def fetch_realtime_data(etf_code):
    """获取ETF实时数据"""
    try:
        df = ak.fund_etf_spot_em()
        if not df.empty:
            filtered_df = df[df['代码'] == etf_code]
            if not filtered_df.empty:
                return filtered_df.iloc[0]
    except Exception as e:
        print(f"获取 {etf_code} 实时数据失败: {e}")
    return None

def calculate_rsi(data, period=14):
    """计算RSI"""
    close_prices = data['收盘']
    if len(close_prices) < period + 1:
        return None
    # 计算价格变化
    deltas = close_prices.diff()
    # 分离涨跌幅
    gains = deltas.where(deltas > 0, 0)
    losses = -deltas.where(deltas < 0, 0)
    # 计算平均涨幅和跌幅（EMA方式）
    avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    # 计算RSI
    if avg_loss == 0:
        return 100.0  # 防止除零错误
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1 + rs))

def calculate_bollinger_bands(data, window=20, std=2):
    """计算布林带"""
    data['Middle Band'] = data['收盘'].rolling(window=window).mean()
    data['Std Dev'] = data['收盘'].rolling(window=window).std()
    data['Upper Band'] = data['Middle Band'] + (data['Std Dev'] * std)
    data['Lower Band'] = data['Middle Band'] - (data['Std Dev'] * std)
    return data

class AlertManager:
    def __init__(self):
        self.alert_records = defaultdict(dict)

    def should_alert(self, etf_code, alert_type):
        record = self.alert_records.get(etf_code, {})
        current_date = datetime.now().date()

        if record.get("last_date") == current_date:
            if alert_type == "overbuy" and record.get("overbuy"):
                return False
            if alert_type == "oversold" and record.get("oversold"):
                return False
        return True

    def update_record(self, etf_code, alert_type):
        current_date = datetime.now().date()
        self.alert_records[etf_code] = {
            "last_date": current_date,
            "overbuy": alert_type == "overbuy",
            "oversold": alert_type == "oversold"
        }



alert_manager = AlertManager()

def monitor_etf(etf_name, etf_code):
    """执行单个ETF监控"""
    # 获取历史数据
    historical_data = fetch_historical_data(etf_code)
    if historical_data is None or len(historical_data) < BOLLINGER_WINDOW:
        return None
    # 获取实时数据
    realtime_data = fetch_realtime_data(etf_code)
    if realtime_data is None:
        return None
    # 将实时数据添加到历史数据中
    latest_close = realtime_data['最新价']
    latest_date = pd.Timestamp.now(tz='Asia/Shanghai').strftime('%Y-%m-%d')
    new_row = pd.DataFrame({'日期': [latest_date], '收盘': [latest_close]})
    historical_data = pd.concat([historical_data, new_row], ignore_index=True)
    # 计算RSI6
    current_rsi = calculate_rsi(historical_data, RSI_PERIOD)
    if current_rsi is None:
        return None

    historical_data = calculate_bollinger_bands(historical_data, BOLLINGER_WINDOW, BOLLINGER_STD)
    upper_band = historical_data['Upper Band'].iloc[-1]
    lower_band = historical_data['Lower Band'].iloc[-1]

    status = f"{etf_name}({etf_code}) | 现价: {latest_close:.3f} | RSI{RSI_PERIOD}: {current_rsi:.1f} | 布林带上轨: {upper_band:.2f} | 布林带下轨: {lower_band:.2f}"

    alert_message = None
    if current_rsi >= RSI_OVERBUY and latest_close >= upper_band:
        if alert_manager.should_alert(etf_code, "overbuy"):
            alert_message = f"🚨 超买警报 {status}"
            alert_manager.update_record(etf_code, "overbuy")
    elif current_rsi <= RSI_OVERSOLD and latest_close <= lower_band:
        if alert_manager.should_alert(etf_code, "oversold"):
            alert_message = f"🚨 超卖警报 {status}"
            alert_manager.update_record(etf_code, "oversold")

    print(f"[{time.strftime('%H:%M')}] {status}")
    return alert_message

def is_trading_time():
    now = pd.Timestamp.now(tz='Asia/Shanghai')
    if now.weekday() >= 5:
        return False
    return ((now.hour == 9 and now.minute >= 30) or
            (10 <= now.hour <= 11) or
            (13 <= now.hour <= 14) or
            (now.hour == 15 and now.minute == 0))

def batch_monitor():
    now = pd.Timestamp.now(tz='Asia/Shanghai')
    if now.hour >= 15 and now.minute > 0:
        print("交易时间已结束")
        mail("hi，交易时间已结束，程序即将退出，今天你赚到钱了吗？")
        os._exit(0)  # 强制退出程序
    if not is_trading_time():
        return

    print(f"\n=== 开始轮次监控 {now.strftime('%Y-%m-%d %H:%M')} ===")
    alert_messages = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(monitor_etf, name, code) for name, code in ETF_LIST]
        for future in futures:
            try:
                result = future.result()
                if result:
                    alert_messages.append(result)
            except Exception as e:
                print(f"任务执行失败: {e}")
    # 如果有警报信息，统一发送邮件
    if alert_messages:
        mail_content = "\n".join(alert_messages)
        mail(mail_content)



if __name__ == "__main__":
    print(f"启动ETF监控系统（共监控{len(ETF_LIST)}个品种）")
    print("=" * 50)

    mail("hi，ETF监控已启动，敬请关注今日推送")
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')

    scheduler.add_job(
        batch_monitor,
        'interval',
        minutes=CHECK_INTERVAL,
        start_date="2024-01-01 09:15:00"
    )


    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("监控已手动停止")
