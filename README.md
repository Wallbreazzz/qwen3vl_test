# qwen3vl_test
## 拉容器
行内平台已经基于镜像创建容器的话忽略这一步，注意修改容器名和镜像 
docker run -itd -u 0  --ipc=host  --privileged --name h00875519_qwen3vl \
 --net=host \
 --shm-size=500g \
 --device /dev/davinci0 \
 --device /dev/davinci1 \
 --device /dev/davinci2 \
 --device /dev/davinci3 \
 --device /dev/davinci4 \
 --device /dev/davinci5 \
 --device /dev/davinci6 \
 --device /dev/davinci7 \
 --device /dev/davinci_manager \
 --device /dev/hisi_hdc \
 --device /dev/devmm_svm \
 -v /usr/local/dcmi:/usr/local/dcmi \
 -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
 -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
 -v /usr/local/Ascend/driver/lib64/:/usr/local/Ascend/driver/lib64/ \
 -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
 -v /etc/ascend_install.info:/etc/ascend_install.info \
 -v /root/.cache:/root/.cache \
 -v /home/:/home/ \
 -it quay.io/ascend/vllm-ascend:v0.19.1rc1 bash

## 容器内起服务
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
export VLLM_ASCEND_ENABLE_DBO=1
export VLLM_ASCEND_ENABLE_NZ=2
export VLLM_ASCEND_ENABLE_DENSE_OPTIMIZE=1
export ATB_OPERATION_EXECUTE_ASYNC=2
export VLLM_USE_MODELSCOPE=True
export PYTORCH_NPU_ALLOC_CONF=max_split_size_mb:256
export PYTHONPATH=/vllm-workspace/vllm:/vllm-workspace/vllm-ascend:$PYTHONPATH
export ASCEND_RT_VISIBLE_DEVICES=1
vllm serve /home/h00875519/qwen3_vl_4b_instruct \
    --host 0.0.0.0 \
    --port 8891 \
    --dtype bfloat16 \
    --max-model-len 16384 \
    --max-num-batched-tokens 16384 \
    --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}' \
    --async-scheduling \
    --allowed-local-media-path /home/h00875519


## curl命令测试
```
curl http://localhost:8891/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
    "model": "/home/h00875519/qwen3_vl_4b_instruct",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    }'
```

原始提示词，注意修改model参数和url参数 
```
curl -w '\nTTFT: %{time_starttransfer}s\nTotal: %{time_total}s\n' \
    http://localhost:8891/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
    "model": "/home/h00875519/qwen3_vl_4b_instruct",
    "messages": [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "file:///home/h00875519/qwen3vl/1.JPG"}},
            {"type": "text", "text": "你是发票结构化识别助手。根据图片识别发票类型并抽取对应字段。只返回合法JSON，不输出解释、分析过程、Markdown。invoiceType 只能取以下值之一：\n区块链发票(深圳)、云南区块链发票、纸质普票、纸质专票、数电普票、电子普票、数电专票、电子专票、纸质普票（卷式）、数电铁路客票、数电航空客票、数电机动车发票、数电二手车发票、机动车发票、二手车发票、电子普票（通行费）、过路费发票、财政医疗(电子)、财政医疗(纸质)、火车高铁票、飞机行程单、定额发票、出租车票、客运汽车票、机打发票、地方通用发票（电子）、地方通用发票（纸质）、其他票据。\n\n按以下优先级判断发票类型，命中高优先级后停止：\n\n1. 区块链发票：\n- 抬头为“深圳电子普通发票”且购方含“电子支付标识” => 区块链发票(深圳)\n- 抬头为“云南省通用电子发票”且购方含“电子支付标识” => 云南区块链发票\n\n2. 增值税发票：\n- 抬头为“电子发票（普通发票）” => 数电普票\n- 抬头为“电子发票（增值税专用发票）” => 数电专票\n- 抬头为“电子发票（铁路电子客票）” => 数电铁路客票\n- 抬头为“电子发票（航空运输电子客票行程单）” => 数电航空客票\n- 抬头为“电子发票（机动车销售统一发票）” => 数电机动车发票\n- 抬头为“电子发票（二手车销售统一发票）” => 数电二手车发票\n- 抬头含“增值税电子普通发票” => 电子普票\n- 抬头含“增值税电子专用发票” => 电子专票\n- 抬头含“电子普通发票”且含“通行日期起”或“通行日期止” => 电子普票（通行费）\n- 抬头含“卷票” => 纸质普票（卷式）\n- 抬头含“增值税普通发票” => 纸质普票\n- 抬头含“增值税专用发票” => 纸质专票\n- 抬头含“机动车” => 机动车发票\n- 抬头含“二手车” => 二手车发票\n\n3. 财政票据：\n- 含“通行费”且含“财政部监制”或“财政票据监制” => 过路费发票\n- 含“电子”且含“财政部监制”或“财政票据监制” => 财政医疗(电子)\n- 含“财政部监制”或“财政票据监制” => 财政医疗(纸质)\n\n4. 费用发票：\n- 含“退票改签时须交回车站”或“买票请到12306” => 火车高铁票\n- 抬头为“航空运输电子客运行程单”且不含“电子发票” => 飞机行程单\n- 抬头含“定额” => 定额发票\n- 含“出租车”或“出租汽车” => 出租车票\n- 含“出口”或“入口”或“入出口”或“起站”或“止站” => 过路费发票\n- 含“乘车”或“发车”或“到站”或“客票”或“客运”或“海运”或“座位号” => 客运汽车票\n- 抬头含“机打” => 机打发票\n\n5. 地方通用发票：\n发票代码为12位数字，且不以“14403”开头，并满足以下任一条件：\n- 第1位是“2”\n- 第1位是“1”且第8位不是“2”\n若满足地方通用发票规则：\n- 含“通行费” => 过路费发票\n- 抬头含“电子” => 地方通用发票（电子）\n- 否则 => 地方通用发票（纸质）\n\n6. 其他：\n以上均不满足 => 其他票据\n\n字段抽取规则：\n\n1. 区块链发票、增值税发票：\nfields 返回：\n{\n  \"invoiceType\": \"发票类型\",\n  \"invoiceCode\": \"发票代码或null\",\n  \"invoiceNumber\": \"发票号码或null\",\n  \"invoiceDate\": \"开票日期或null\",\n  \"totalAmount\": \"价税合计或null\",\n  \"checkCode\": \"校验码或null\"\n}\n\n2. 火车高铁票：\nfields 返回：\n{\n  \"invoiceType\": \"发票类型\",\n  \"trafficNum\": \"票号或null\",\n  \"trafficDate\": \"乘车日期或null\",\n  \"totalAmount\": \"合计金额或null\"\n}\n\n3. 飞机行程单：\nfields 返回：\n{\n  \"invoiceType\": \"发票类型\",\n  \"trafficNum\": \"电子票号或null\",\n  \"trafficDate\": \"乘机日期或null\",\n  \"totalAmount\": \"合计金额或null\"\n}\n\n4. 出租车票：\nfields 返回：\n{\n  \"invoiceType\": \"发票类型\",\n  \"invoiceCode\": \"发票代码或null\",\n  \"invoiceNumber\": \"发票号码或null\",\n  \"trafficDate\": \"乘车日期或null\",\n  \"totalAmount\": \"金额或null\",\n  \"boardingTime\": \"上车时间或null\",\n  \"alightingTime\": \"下车时间或null\",\n  \"carNumber\": \"车牌号或null\"\n}\n\n5. 定额发票、机打发票、地方通用发票、过路费发票、客运汽车票：\n适用类型：定额发票、机打发票、地方通用发票（电子）、地方通用发票（纸质）、过路费发票、客运汽车票。\nfields 返回：\n{\n  \"invoiceType\": \"发票类型\",\n  \"invoiceCode\": \"发票代码或null\",\n  \"invoiceNumber\": \"发票号码或null\",\n  \"invoiceDate\": \"开票日期或null\",\n  \"totalAmount\": \"合计金额或null\"\n}\n\n6. 财政票据：\n适用类型：财政医疗(电子)、财政医疗(纸质)。\nfields 返回：\n{\n  \"invoiceCode\": \"发票代码或null\",\n  \"invoiceNumber\": \"发票号码或null\",\n  \"invoiceDate\": \"开票日期或null\",\n  \"totalAmount\": \"合计金额或null\",\n  \"payer\": \"交款人或null\"\n}\n\n7. 未配置字段类型：\nfields 返回 {}。\n\n字段规范：\n- 看不清、不存在、无法确认的字段返回 null。\n- 日期统一 yyyy-MM-dd。\n- 时间尽量返回 HH:mm；如果票面包含日期和时间，可以返回 yyyy-MM-dd HH:mm。\n- 金额去掉货币符号、中文单位和千分位逗号，保留两位小数，作为字符串返回。\n- 不要输出未定义字段。"}
        ]}
    ],
    "max_tokens": 100
    }'
```

## 压测
压测脚本用的是原始提示词，可以修改脚本更换提示词 
压测脚本用的是同一张图片，如果项贴近真实业务场景可以用多张图片 
单请求
```
python bench_invoice.py single
```
单并发多请求
```
python bench_invoice.py bench 1 20
```
多并发多请求
```
python bench_invoice.py bench 5 50
```
