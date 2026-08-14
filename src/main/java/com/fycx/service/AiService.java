package com.fycx.service;

import com.fycx.controller.request.AiReportRequest;
import com.fycx.controller.request.ChatRequest;
import com.fycx.controller.response.PageResult;
import com.fycx.entity.AiReport;
import com.fycx.entity.PromptTemplate;

import java.util.List;

/**
 * AI 解读服务: 三层Prompt工程(角色设定+数据注入+输出约束) + 大模型调用 + 对话记录
 */
public interface AiService {

    /** 启用的提示词模板 */
    List<PromptTemplate> listTemplates();

    /** 生成财报解读简报 */
    AiReport generateReport(AiReportRequest req);

    /** 上下文感知的多轮对话 */
    AiReport chat(ChatRequest req);

    /** 报告记录分页 */
    PageResult<AiReport> listReports(Integer companyId, int page, int size);

    /** 报告详情 */
    AiReport getReport(Long reportId);
}
