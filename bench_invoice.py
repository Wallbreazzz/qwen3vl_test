import time
import json
import urllib.request
import base64
import os
import sys

MODEL_PATH = "/home/h00875519/qwen3_vl_4b_instruct"
IMAGE_PATH = "/home/h00875519/qwen3vl/1.JPG"
API_URL = "http://localhost:8891/v1/chat/completions"

PROMPT = """你是发票结构化识别助手。根据图片识别发票类型并抽取对应字段。只返回合法JSON，不输出解释、分析过程、Markdown。invoiceType 只能取以下值之一：
区块链发票(深圳)、云南区块链发票、纸质普票、纸质专票、数电普票、电子普票、数电专票、电子专票、纸质普票（卷式）、数电铁路客票、数电航空客票、数电机动车发票、数电二手车发票、机动车发票、二手车发票、电子普票（通行费）、过路费发票、财政医疗(电子)、财政医疗(纸质)、火车高铁票、飞机行程单、定额发票、出租车票、客运汽车票、机打发票、地方通用发票（电子）、地方通用发票（纸质）、其他票据。

按以下优先级判断发票类型，命中高优先级后停止：

1. 区块链发票：
- 抛头为"深圳电子普通发票"且购方含"电子支付标识" => 区块链发票(深圳)
- 抛头为"云南省通用电子发票"且购方含"电子支付标识" => 云南区块链发票

2. 增值税发票：
- 抛头为"电子发票（普通发票）" => 数电普票
- 抛头为"电子发票（增值税专用发票）" => 数电专票
- 抛头为"电子发票（铁路电子客票）" => 数电铁路客票
- 抛头为"电子发票（航空运输电子客票行程单）" => 数电航空客票
- 抛头为"电子发票（机动车销售统一发票）" => 数电机动车发票
- 抛头为"电子发票（二手车销售统一发票）" => 数电二手车发票
- 抛头含"增值税电子普通发票" => 电子普票
- 抛头含"增值税电子专用发票" => 电子专票
- 抛头含"电子普通发票"且含"通行日期起"或"通行日期止" => 电子普票（通行费）
- 抛头含"卷票" => 纸质普票（卷式）
- 抛头含"增值税普通发票" => 纸质普票
- 抛头含"增值税专用发票" => 纸质专票
- 抛头含"机动车" => 机动车发票
- 抛头含"二手车" => 二手车发票

3. 财政票据：
- 含"通行费"且含"财政部监制"或"财政票据监制" => 过路费发票
- 含"电子"且含"财政部监制"或"财政票据监制" => 财政医疗(电子)
- 含"财政部监制"或"财政票据监制" => 财政医疗(纸质)

4. 费用发票：
- 含"退票改签时须交回车站"或"买票请到12306" => 火车高铁票
- 抛头为"航空运输电子客运行程单"且不含"电子发票" => 飞机行程单
- 抛头含"定额" => 定额发票
- 含"出租车"或"出租汽车" => 出租车票
- 含"出口"或"入口"或"入出口"或"起站"或"止站" => 过路费发票
- 含"乘车"或"发车"或"到站"或"客票"或"客运"或"海运"或"座位号" => 客运汽车票
- 抛头含"机打" => 机打发票

5. 地方通用发票：
发票代码为12位数字，且不以"14403"开头，并满足以下任一条件：
- 第1位是"2"
- 第1位是"1"且第8位不是"2"
若满足地方通用发票规则：
- 含"通行费" => 过路费发票
- 抛头含"电子" => 地方通用发票（电子）
- 否则 => 地方通用发票（纸质）

6. 其他：
以上均不满足 => 其他票据

字段抽取规则：

1. 区块链发票、增值税发票：
fields 返回：
{
  "invoiceType": "发票类型",
  "invoiceCode": "发票代码或null",
  "invoiceNumber": "发票号码或null",
  "invoiceDate": "开票日期或null",
  "totalAmount": "价税合计或null",
  "checkCode": "校验码或null"
}

2. 火车高铁票：
fields 返回：
{
  "invoiceType": "发票类型",
  "trafficNum": "票号或null",
  "trafficDate": "乘车日期或null",
  "totalAmount": "合计金额或null"
}

3. 飞机行程单：
fields 返回：
{
  "invoiceType": "发票类型",
  "trafficNum": "电子票号或null",
  "trafficDate": "乘机日期或null",
  "totalAmount": "合计金额或null"
}

4. 出租车票：
fields 返回：
{
  "invoiceType": "发票类型",
  "invoiceCode": "发票代码或null",
  "invoiceNumber": "发票号码或null",
  "trafficDate": "乘车日期或null",
  "totalAmount": "金额或null",
  "boardingTime": "上车时间或null",
  "alightingTime": "下车时间或null",
  "carNumber": "车牌号或null"
}

5. 定额发票、机打发票、地方通用发票、过路费发票、客运汽车票：
适用类型：定额发票、机打发票、地方通用发票（电子）、地方通用发票（纸质）、过路费发票、客运汽车票。
fields 返回：
{
  "invoiceType": "发票类型",
  "invoiceCode": "发票代码或null",
  "invoiceNumber": "发票号码或null",
  "invoiceDate": "开票日期或null",
  "totalAmount": "合计金额或null"
}

6. 财政票据：
适用类型：财政医疗(电子)、财政医疗(纸质)。
fields 返回：
{
  "invoiceCode": "发票代码或null",
  "invoiceNumber": "发票号码或null",
  "invoiceDate": "开票日期或null",
  "totalAmount": "价税合计或null",
  "payer": "交款人或null"
}

7. 未配置字段类型：
fields 返回 {}。

字段规范：
- 看不清、不存在、无法确认的字段返回 null。
- 日期统一 yyyy-MM-dd。
- 时间尽量返回 HH:mm；如果票面包含日期和时间，可以返回 yyyy-MM-dd HH:mm。
- 金额去掉货币符号、中文单位和千分位逗号，保留两位小数，作为字符串返回。
- 不要输出未定义字段。"""


def load_image_b64(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = f"image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{b64}"


def build_request_body(image_url, stream=False):
    return json.dumps({
        "model": MODEL_PATH,
        "messages": [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": PROMPT},
            ]}
        ],
        "max_tokens": 100,
        "stream": stream,
    }).encode()


def bench_single(image_url, use_stream=True):
    data = build_request_body(image_url, stream=use_stream)
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})

    start = time.time()
    first_token_time = None
    content = ""

    resp = urllib.request.urlopen(req)
    if use_stream:
        for line in resp:
            line = line.decode().strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:]
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
                delta = obj["choices"][0]["delta"]
                if "content" in delta and delta["content"]:
                    if first_token_time is None:
                        first_token_time = time.time()
                    content += delta["content"]
            except json.JSONDecodeError:
                pass
    else:
        body = json.loads(resp.read().decode())
        content = body["choices"][0]["message"]["content"]
        first_token_time = time.time()

    end = time.time()
    return {
        "content": content,
        "ttft": first_token_time - start if first_token_time else None,
        "e2e": end - start,
    }


def bench_concurrent(image_url, concurrency, total_requests, use_stream=True):
    import concurrent.futures

    results = []
    start_all = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(bench_single, image_url, use_stream) for _ in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.time() - start_all

    ttfts = [r["ttft"] for r in results if r["ttft"] is not None]
    e2es = [r["e2e"] for r in results]

    print("\n===== Benchmark Results =====")
    print(f"Concurrency:         {concurrency}")
    print(f"Total requests:      {total_requests}")
    print(f"Total time:          {total_time:.2f}s")
    print(f"Throughput:          {total_requests / total_time:.2f} req/s")
    if ttfts:
        sorted_ttfts = sorted(ttfts)
        print(f"Mean TTFT:           {sum(ttfts) / len(ttfts):.3f}s")
        print(f"P50 TTFT:            {sorted_ttfts[len(sorted_ttfts) // 2]:.3f}s")
        print(f"P99 TTFT:            {sorted_ttfts[int(len(sorted_ttfts) * 0.99)]:.3f}s")
    sorted_e2es = sorted(e2es)
    print(f"Mean E2E:            {sum(e2es) / len(e2es):.3f}s")
    print(f"P50 E2E:             {sorted_e2es[len(sorted_e2es) // 2]:.3f}s")
    print(f"P99 E2E:             {sorted_e2es[int(len(sorted_e2es) * 0.99)]:.3f}s")
    print("=" * 30)

    for i, r in enumerate(results[:3]):
        print(f"\n--- Sample {i + 1} ---")
        print(f"E2E: {r['e2e']:.3f}s  TTFT: {r['ttft']:.3f}s" if r['ttft'] else f"E2E: {r['e2e']:.3f}s")
        print(f"Response: {r['content']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"

    with open(IMAGE_PATH, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(IMAGE_PATH)[1].lower().lstrip(".")
    mime = f"image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    image_url = f"data:{mime};base64,{b64}"

    if mode == "single":
        print("Running single request (stream mode)...")
        r = bench_single(image_url, use_stream=True)
        print(f"\nTTFT: {r['ttft']:.3f}s")
        print(f"E2E:  {r['e2e']:.3f}s")
        print(f"Response: {r['content']}")

    elif mode == "bench":
        concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        total = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        print(f"Running bench: concurrency={concurrency}, total={total}...")
        bench_concurrent(image_url, concurrency, total, use_stream=True)

    else:
        print(f"Usage: python bench_invoice.py [single|bench [concurrency [total]]]")
        print(f"  single  - one request, print TTFT + E2E + response")
        print(f"  bench 1 20  - 1 concurrent, 20 requests")
        print(f"  bench 5 50  - 5 concurrent, 50 requests")
