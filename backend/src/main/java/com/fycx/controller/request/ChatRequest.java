package com.fycx.controller.request;

import lombok.Data;

import java.util.List;

/**
 * AI 追问对话请求(上下文感知)
 */
@Data
public class ChatRequest {
    private Integer companyId;
    private Integer fiscalYear;
    private String reportPeriod = "年报";
    private String question;
    private List<ChatTurn> history;    // 可选: 历史对话
}
