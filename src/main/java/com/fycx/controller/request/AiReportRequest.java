package com.fycx.controller.request;

import lombok.Data;

/**
 * AI 简报生成请求
 */
@Data
public class AiReportRequest {
    private Integer companyId;
    private Integer fiscalYear;
    private String reportPeriod = "年报";
    private String extraInstruction;   // 可选: 附加要求
}
