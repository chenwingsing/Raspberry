import akshare as ak
from datetime import datetime
import requests
from bs4 import BeautifulSoup

webhook_url = "xxxxxx"

def send_to_wechat(msg):
    # 构造企业微信消息
    data = {
        "msgtype": "text",
        "text": {
            "content": msg
        }
    }

    try:
        # 发送请求到企业微信机器人
        response = requests.post(webhook_url, json=data, timeout=5)
        if response.status_code == 200:
            print("消息发送成功！")
        else:
            print(f"消息发送失败，状态码：{response.status_code}")
    except Exception as e:
        print("发送消息时出错:", e)

def gettemp():
    # 设置请求头，模拟浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        "Connection": "keep-alive"
    }


    # 发送 HTTP 请求
    url = "https://youzhiyouxing.cn/data"
    response = requests.get(url, headers=headers)

    # 检查请求是否成功
    if response.status_code != 200:
        print("无法访问网站，请检查网址或网络连接。")
    else:
        # 解析网页内容
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找包含温度值的 div 标签
        temperature_div = soup.find("div", class_="tw-text-[40px] tw-font-semibold")

        if temperature_div:
            # 提取温度值并打印
            temperature = temperature_div.text.strip()
            return temperature
            #print("当前温度:", temperature)
        else:
            print("未找到温度值，请检查目标网站的 HTML 结构是否已更新。")

def get_stock_data():
    # 获取当前日期
    today = datetime.now().strftime("%Y年%m月%d日")

    try:
        # 获取沪深京指数实时行情数据
        index_data = ak.stock_zh_index_spot_em(symbol="沪深重要指数")

        # 筛选出上证指数和创业板指数
        shanghai_index = index_data[index_data["名称"] == "上证指数"].iloc[0]
        chnext_index = index_data[index_data["名称"] == "创业板指"].iloc[0]

        # 提取所需数据
        shanghai_close = shanghai_index["最新价"]
        shanghai_change_percent = shanghai_index["涨跌幅"]
        chnext_close = chnext_index["最新价"]
        chnext_change_percent = chnext_index["涨跌幅"]

        #计算成交总额
        index_data.loc[
            index_data["名称"] == "上证指数", "成交额"
        ] = (
                index_data.loc[index_data["名称"] == "上证指数", "成交额"] / 1e8
        ).round(1)

        index_data.loc[
            index_data["名称"] == "深证成指", "成交额"
        ] = (
                index_data.loc[index_data["名称"] == "深证成指", "成交额"] / 1e8
        ).round(1)

        # 筛选出相关数据
        shanghai_stock = index_data[index_data["名称"] == "上证指数"]
        shenzhen_stock = index_data[index_data["名称"] == "深证成指"]

        # 计算沪深总交易额
        total_transaction = (
                shanghai_stock["成交额"].values[0] + shenzhen_stock["成交额"].values[0]
        ).round(1)
        # 格式化输出
        temp = gettemp()
        message =(
            f"{today}，成交额{total_transaction/10000:.4f}万亿，上证指数{shanghai_close:.2f}，收{'涨' if shanghai_change_percent > 0 else '跌'}{abs(shanghai_change_percent):.2f}%，创业板{chnext_close:.2f}，收{'涨' if chnext_change_percent > 0 else '跌'}{abs(chnext_change_percent):.2f}%，知行温度计为{temp}")
        send_to_wechat(message)
    except Exception as e:
            print("获取数据时出错:", e)

if __name__ == "__main__":
    get_stock_data()


