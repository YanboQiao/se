尊敬的 **徐晶老师**：

您好！作为本门《软件工程课程设计》项目的组长，我谨就**基于大模型的软工课设课程助手**当前作业要求，提出以下意见与建议。我们深知课程目标在于培养前沿视野，但现阶段的任务规模与技术门槛已远超大三本科生的可承受范围，恐难以达到教学初衷，恳请您审慎斟酌并适度调整。

---

## 一、成本与资源：训练 / 微调 LLM 的现实代价

1. **计算成本动辄上万美元**
   以 70 B 级别模型为例，社区估算仅*一次完整训练*即需 **≈8.5 万美元**；若含反复试验与故障回滚，费用更高。([Hacker News][1])
   更大规模如 GPT-3（175 B）单次训练成本已高达 **50–460 万美元**，远非 6 人课设经费所能支撑。([CUDO Compute][2])

2. **按时计费 GPU 亦非“零花钱”**
   即使采用云端租赁，一张 A100 /SXM4 GPU 每小时 **0.35–1.60 美元**；常见 8 卡节点一晚实验费即约 30–120 美元，连续几周即可累积上千至上万美元不等。([Vast AI][3])

---

## 二、能力与课程定位：与学生现有技能严重错位

1. **课程属性并非机器学习**
   软件工程课程核心是**过程管理、需求分析、设计规范**等，而非深度学习模型开发。强行要求训练 / 微调 LLM，与既定教学大纲脱节。
2. **缺乏必要的算法与硬件基础**
   大三同学尚未系统学习分布式训练、张量并行或高性能 GPU 调优等知识，更无专用服务器；即便商用 QLoRA 等轻量方案，也需精通 CUDA 与推理引擎，难以在短学期内掌握。

---

## 三、数据与合规：难以获取符合版权与质量要求的训练集

开源大模型通常**仅提供权重而非原始数据**；高质量教材、论文与课程讲义多受版权保护，采集、标注乃至清洗流程均耗时耗资，且涉及个人隐私与学校资源授权。

---

## 四、行业实践：主流做法是 RAG / Prompt Engineering，而非自训模型

近一年业界普遍采用 **Retrieval-Augmented Generation (RAG)** 或系统提示词优化，让现成模型调用外部知识库即可满足定制需求，且几乎零训练成本，性价比远超自研模型。([IBM - United States][4], [The world's open source leader][5])

---

## 五、建议

1. **将目标下调为「基于现成大模型的 RAG 课程助手」**：

   * 学生专注于需求梳理、知识库构建与 API 调用，符合软工课程定位；
   * 计算开销可控，避免无谓硬件投入。
2. **提供公用 GPU / 推理 API 配额**：若确需实验微调，可由学院统一申请小规模配额，供同学体验流程而非完成整机训练。
3. **在评分标准中淡化模型性能占比**：聚焦文档编写、项目管理与协作流程，鼓励同学展示软工方法论。

---

我们理解课程创新初衷，但亦期望任务与能力相匹配，以确保教学质量与学生学习体验。恳请老师考虑上述事实与建议，适度调整作业要求。感谢您抽空阅读，期待与您进一步讨论！


乔彦博
2025 年 5 月 6 日

[1]: https://news.ycombinator.com/item?id=35391469&utm_source=chatgpt.com "His estimate is that you could train a LLaMA-7B scale model for ..."
[2]: https://www.cudocompute.com/blog/what-is-the-cost-of-training-large-language-models?utm_source=chatgpt.com "What is the cost of training large language models? - CUDO Compute"
[3]: https://vast.ai/pricing/gpu/A100-SMX4?utm_source=chatgpt.com "A100 SXM4 GPU Rental | Vast.ai"
[4]: https://www.ibm.com/think/topics/rag-vs-fine-tuning?utm_source=chatgpt.com "RAG vs. Fine-tuning - IBM"
[5]: https://www.redhat.com/en/topics/ai/rag-vs-fine-tuning?utm_source=chatgpt.com "RAG vs. fine-tuning - Red Hat"
