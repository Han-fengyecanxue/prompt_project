# 上手指南:Prompt 工程 · 云端 API · 本地模型 · 文生图

> 配套项目:基于 Prompt 工程的上市公司财报解读与行业对标系统(Spring Boot + Vue3)
> 适用:论文撰写、答辩演示、日常自学。所有示例都可在本机直接跑通。

---

## 0. 指南地图(先看这段)

| 章节 | 你学会后能做什么 | 用时 |
|---|---|---|
| 一、Prompt 工程 | 看懂/改进本项目"三层 Prompt",自己能写出高质量提示词 | 20 分钟 |
| 二、云端 API | 申请 DeepSeek/通义 key,把本系统从 mock 切换成真大模型 | 20 分钟 |
| 三、本地模型 | 装 Ollama,离线跑 DeepSeek-R1/Qwen,不花钱接入系统 | 30 分钟 |
| 四、文生图 Prompt | 用公式写图生图提示词,给论文/海报出概念图 | 20 分钟 |
| 五、速查表 | 常见命令/报错/接线清单,卡住时先翻这里 | 随用随查 |

一句话总纲:**Prompt 是"把需求说清楚"的能力;API 是"花钱租模型";本地模型是"自己养模型";文生图是"用同一套 Prompt 功夫指挥画画模型"。** 学会前两者,后两者只是换了模型。

---

## 一、Prompt 工程基础

### 1.1 什么是 Prompt,为什么要"工程化"

Prompt(提示词)是你发给大模型的一段指令。日常聊天随口一问也能得到结果,但**要稳定、可靠、可复现地得到专业结果,就必须工程化**——因为本项目是给学生/投资者看的财报解读,模型一旦"自由发挥"就会编造数字(幻觉),这在金融场景是不可接受的。

工程化的核心思想:**把大模型当作一个能力很强但很"听话"的实习生,你交代任务必须包含——他是谁(角色)、做什么(目标)、材料在哪(数据)、按什么格式交作业(输出约束)、不许做什么(边界)。**

### 1.2 一个万能 Prompt 结构

```
【角色】你是一位……(资历、专长、风格)
【任务】请完成……(要解决的具体问题)
【材料】以下是唯一可信的数据/文本:……(放在 {{ }} 或 JSON 里)
【要求】
  1. 只能使用材料中的数据,不得编造/推测
  2. 输出格式:……(标题结构 / Markdown / JSON 字段)
  3. 篇幅:……
  4. 数据缺失时,明确说"数据不足",不许猜
【输出示例】(可选,Few-shot 给它看一个理想回答的样子)
```

### 1.3 本项目怎么做的:三层 Prompt(可直接写进论文)

本项目把上面的结构拆成数据库里可维护的三条模板(`prompt_template` 表,类型分别为 `角色设定 / 数据注入 / 输出约束`),由 `AiServiceImpl` 运行时拼接,再把**系统精确计算出的指标与行业对标数据**以 JSON 注入 `{data_json}` 占位符:

1. **角色设定**:你是一位资深上市公司财务分析师,拥有 CFA 资质与 10 年以上 A 股财报分析经验……结论必须有数据支撑。
2. **数据注入**:以下是系统精确计算出的该公司 {fiscalYear} 年财务指标与行业对标数据(JSON),**这是本次分析唯一可信的数据来源**:{data_json} 行业对标口径:均值/中位数/P25/P75 基于同行业同一年度计算……
3. **输出约束**:只能使用注入数据,严禁编造;报告固定六段结构(概览/盈利/成长/风险/估值/结论);每章必须引用具体数值与对标结果(如 ROE 25.3%,高于行业中位数 18.2%);给出综合评级;800 字内;数据缺失必须明说。

> 为什么这样设计能防幻觉?
> ① 数据与知识分离——需要精确的数字全部由**程序**算好塞进 Prompt,模型只做"解读"不参与"计算";
> ② 输出约束里明确"只能使用注入数据"并给了反例;
> ③ 每次调用会把注入的数据上下文存库(`ai_report.context` 字段),**事后可审计模型有没有捏造**。
> 这一点是论文里"防幻觉设计"的核心论据。

### 1.4 打磨 Prompt 的实用技巧

| 技巧 | 说明 | 反例 → 正例 |
|---|---|---|
| 具体化 | 少用"分析一下",多用动词+对象+范围 | "分析一下" → "从盈利、成长、风险三个维度解读该公司 2025 年财报" |
| 角色约束 | 设定身份与文风,输出更稳定 | 无角色 → "以 CFA 分析师身份,面向普通投资者,用通俗语言" |
| 给材料 | 需要精确信息时**放进 Prompt**,别指望模型"记得" | "茅台 ROE 多少?" → 注入数据后"根据注入数据回答" |
| 给格式 | 表格/JSON/标题结构都能约束 | "输出要点" → "按一~六六段输出,每段先结论后数据" |
| 防幻觉 | 声明数据唯一来源 + 缺失明说 + 给反例 | 无 → "若数据中不包含所需信息,请明确说明,不得编造" |
| Few-shot | 给 1~2 个理想回答示例,风格立刻对齐 | 抽象描述 → "参考示例:……" |
| 温度调低 | 财报等事实类任务 temperature 0.2~0.4 | 默认偏高 → `ai.temperature=0.3`(项目默认) |

### 1.5 迭代工作流

1. 写第一版 → 2. 跑 3~5 个不同公司/年份样例 → 3. 找共性失败(编数字?格式乱?漏章节?) → 4. 改对应层模板 → 5. 回归。本项目改了模板**不用改代码**,重启即可(答辩时可直接演示"换 Prompt 看效果"——这是 Prompt 工程系统最大的卖点)。

---

## 二、云端 API(花钱租模型)

### 2.1 基本概念

- **API Key**:你的账号凭证,请求时放在请求头 `Authorization: Bearer <你的key>`。**Key 等于密码,别提交到 Git、别发群里。**
- **Base URL**:服务商的接口地址。绝大多数国内厂商兼容 OpenAI 协议,统一为 `https://xxx/v1`。
- **模型名(model)**:每次请求指定,如 `deepseek-chat`、`qwen-plus`。

一次标准请求(OpenAI 兼容协议):

```bash
curl https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-你的key" \
  -d '{
    "model": "deepseek-chat",
    "temperature": 0.3,
    "messages": [
      {"role": "system", "content": "你是一位严谨的财务分析师……"},
      {"role": "user", "content": "请解读以下数据:{...}"}
    ]
  }'
```

### 2.2 怎么选(2026 年常见,价格/额度会变,以官网为准)

| 厂商 | 模型示例 | 特点 | Key 申请入口 |
|---|---|---|---|
| DeepSeek | deepseek-chat / deepseek-reasoner | 中文好、便宜,兼容 OpenAI | platform.deepseek.com |
| 阿里通义 | qwen-plus / qwen-max | 新用户送额度,百炼平台 | bailian.console.aliyun.com |
| 智谱 GLM | glm-4-plus | 中文生态好 | open.bigmodel.cn |
| 月之暗面 Kimi | moonshot-v1 | 长文本强 | platform.moonshot.cn |
| OpenAI | gpt-4o-mini | 需外网+绑卡 | platform.openai.com |

> 学生做省级项目:优先 **DeepSeek**(便宜)或 **通义千问**(新用户免费额度)。理由:本系统只是把几百~几千字的指标 JSON 注入后生成 800 字报告,单次消耗 token 极小,一个月花费通常几块钱以内。

### 2.3 本项目接入云端(3 步)

1. 拿到 key 后,编辑后端配置(已 gitignore,不会提交):
   `src/main/resources/config/application-development.properties`
   ```properties
   ai.provider=openai        # 把 mock 改成 openai
   ai.base-url=https://api.deepseek.com/v1
   ai.api-key=sk-你的key
   ai.model=deepseek-chat
   ai.temperature=0.3
   ```
2. 重新打包并重启后端(见 README):`.\mvnw.cmd -DskipTests package && java -jar target\prompt_project-0.0.1-SNAPSHOT.jar`
3. 验证:`curl http://localhost:8091/api/health` 看 `aiProvider:"openai"`,然后前端「AI 解读」页点生成。

换通义只需改两行:`ai.base-url=https://dashscope.aliyuncs.com/compatible-mode/v1`、`ai.model=qwen-plus`。**代码零改动**——因为 AiService 只认 OpenAI 兼容协议。

### 2.4 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 401 Unauthorized | key 错误/没填 | 检查 ai.api-key;确认没多余空格 |
| 429 Too Many Requests | 限流/余额不足 | 等一下重试;检查账户余额;调低并发 |
| 超时(本项目默认 60s) | 网络慢/模型忙 | `ai.timeout-seconds=120`;换 base-url |
| 返回内容为空/乱码 | 请求头缺编码 | 确认 Content-Type: application/json |

---

## 三、本地模型(离线免费跑)

### 3.1 为什么用本地模型

答辩现场**可能没网**;财报数据属于敏感信息不想出本机;长期跑也不花钱。代价是:需要一台配置尚可的电脑,模型能力弱于云端旗舰。

### 3.2 推荐路线:Ollama(傻瓜式)

1. 官网 ollama.com 下载安装(Windows 直接装)。
2. 拉模型(按显存选):
   ```bash
   ollama run qwen2.5:7b        # 入门首选,8G 内存+4G 显存即可,中文不错
   # 或
   ollama run deepseek-r1:8b    # 带思维链,数学推理强(本项目解读够用)
   # 显存够大可上 qwen2.5:14b / qwen2.5:32b;纯 CPU 用 3b/7b 也能跑,慢些
   ```
   跑起来后 Ollama 会自动占一个本地端口 **11434**。
3. 它自带 OpenAI 兼容接口,直接 curl 就能测:
   ```bash
   curl http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"你好"}]}'
   ```

### 3.3 本项目接入 Ollama(同样只改配置)

```properties
ai.provider=openai                              # 保持不变:openai 即"兼容协议"
ai.base-url=http://localhost:11434/v1           # 指向本地 Ollama
ai.api-key=ollama                               # 随便填,本地不校验
ai.model=qwen2.5:7b                             # 必须是已 pull 的模型名
```
重启后端即生效。**mock → 云端 DeepSeek → 本地 Ollama,三者切换只改一个配置文件**——这就是"AI 供应商可插拔"设计,建议写进论文的架构章节。

### 3.4 对比建议(答辩话术)

| 维度 | 云端(DeepSeek) | 本地(Ollama) | Mock(默认) |
|---|---|---|---|
| 联网 | 需要 | 不需要 | 不需要 |
| 成本 | 几分钱/千次级别 | 0 | 0 |
| 效果 | 好 | 中(小模型) | 预设文案(仅演示 UI) |
| 适用 | 论文实验、正式使用 | 答辩演示、数据敏感场景 | 开发调试 |

> 论文研究按 [真实财报数据论文研究指南](Prompt工程深化研究与系统扩展方案.md) 执行。数值校验器仅用于候选筛查，不能代替年报核验和人工标注。

---

## 四、Prompt 优化文生图

### 4.1 原理一句话

文生图模型(扩散模型)把文字"翻译"成画面。它**不懂语法只懂关键词**,所以画质好坏 90% 取决于你的 Prompt 里堆了哪些"词块"和"风格锚点";另 10% 是负向提示词与参数。

### 4.2 工具选择

| 场景 | 工具 | 说明 |
|---|---|---|
| 免费在线(中文) | 通义万相、即梦、文心一格 | 网页直接用,适合给论文配概念图 |
| 云端 API | 通义万相(DashScope)、OpenAI DALL·E 3 | 可编程批量生成 |
| 本地免费 | Stable Diffusion WebUI / ComfyUI | 需显卡(6G+),可控性最强 |

### 4.3 万能公式(重点背这一段)

```
[主体 Subject] + [动作/状态] + [风格 Style] + [构图/视角 View] + [光线/氛围 Lighting] + [材质/细节 Detail] + [画质词 Quality] + [画幅 Ratio]
```

示例(英文最稳,中文模型可写中文):

```
一只戴金丝眼镜的柴犬会计正在翻阅财报, 桌上散落图表, 
赛博朋克+中国风海报风格, 特写+仰视构图, 工作室光, 高细节,
8k, 超清, 电影感 —— (positive)

模糊, 低清, 畸形, 多余手指, 水印, 文字错乱 —— (negative 负向词)
```

要点:
- **风格词决定"画风"**:水彩 / 3D 渲染 / 油画 / 国潮插画 / 扁平设计 / 写实摄影,一次只混 1~2 种,混多了脏。
- **画质词放最后**:`highly detailed, 8k, sharp focus, masterpiece`。
- **写实/人物时负向词必加**:`extra fingers, deformed hands, blurry, watermark, text`。
- **构图词**控制镜头感:`close-up(特写) / wide shot(远景) / from above(俯视) / eye level`。
- **一次只改一个变量**:固定 seed,改一个词对比,才知道哪个词起效(迭代调优法)。

### 4.4 本项目/论文可直接抄的模板

1. **系统架构图风格封面**(答辩 PPT/论文封面背景):
   `data flow architecture diagram, financial system, server room with glowing data streams, minimal tech poster, dark blue theme, wide shot, cinematic light, ultra detailed, 16:9`
2. **AI + 金融概念图**(论文"研究背景"配图):
   `robot analyst examining glowing financial charts in a library, neural network light threads, soft depth of field, elegant fintech illustration, 8k`
3. **数据可视化海报**(系统介绍页):
   `dashboard UI mockup floating in 3D space, line charts and bar charts, clean fintech style, soft studio lighting, high detail, isometric view`
4. **白酒行业营收柱状图装饰**(实验截图旁):
   `Chinese baijiu bottles aligned like bar chart, warm amber light, product photography style, clean white background`
5. 中文可先写中文再让大模型翻成英文(给第四章第一节的角色模板即可),翻译时注意把"形容词词块"保持逗号分隔。

> 合规提醒:论文若用 AI 生成图,按学校要求在图注注明"(AI 生成,提示词见附录)"即可;本项目数据图表(折线/柱状)由系统 ECharts 真实生成,不属于 AI 生成。

---

## 五、速查表

### 5.1 本项目接线清单(大模型接入排错顺序)

```
1. 配置:application-development.properties 的 provider/base-url/api-key/model
2. 重启:后端 java -jar……,看 backend.log 无报错
3. 直测:curl http://localhost:8091/api/health  → aiProvider 是否正确
4. 测接口:curl -X POST localhost:8091/api/ai/report -d '{"companyId":17,"fiscalYear":2025}' -H "Content-Type: application/json"
5. 看前端:http://localhost:5173 → AI 解读
6. 还不行 → 看 backend.err.log / 厂商控制台用量
```

### 5.2 常用命令

```bash
# 云端直测(DeepSeek)
curl https://api.deepseek.com/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer sk-xxx" -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}]}'

# 本地直测(Ollama)
ollama list                      # 已装模型
ollama pull qwen2.5:7b           # 下载
ollama run qwen2.5:7b            # 交互对话
curl http://localhost:11434/v1/chat/completions -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"你好"}]}'
```

### 5.3 报错速查

| 报错 | 意思 | 怎么办 |
|---|---|---|
| 401 | key 无效 | 检查 key/空格/是否过期 |
| 429 | 限流或没钱 | 稍等;充值;换小模型 |
| connection refused 11434 | Ollama 没开 | `ollama serve` 或重开 Ollama |
| model not found | 模型没下 | `ollama pull 对应名字` |
| 报告里数字对不上 | 幻觉 | 检查输出约束模板;换更强模型;跑 report_validator.py 审计 |

---

## 附:本项目相关文件位置

- 三层 Prompt 模板数据:`sql/01_schema.sql` 中 `prompt_template` 表的 3 行插入语句
- Prompt 拼接逻辑:`src/main/java/com/fycx/service/impl/AiServiceImpl.java`
- AI 供应商配置:`src/main/resources/config/application-development.properties`(mock/openai 切换)
- 幻觉自动校验:`tools/report_validator.py`;实验图表:`tools/plot_hallucination.py`、`docs/eval_data.csv`
- 本指南转 Word:在 backend 目录执行 `py tools/md2docx.py docs/上手指南_Prompt与模型.md`
