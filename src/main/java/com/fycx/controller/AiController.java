package com.fycx.controller;

import com.fycx.controller.request.AiReportRequest;
import com.fycx.controller.request.ChatRequest;
import com.fycx.controller.response.CommonResponse;
import com.fycx.controller.response.PageResult;
import com.fycx.entity.AiReport;
import com.fycx.entity.PromptTemplate;
import com.fycx.service.AiService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * AI 解读接口: Prompt模板 / 简报生成 / 追问对话 / 报告记录
 */
@RestController
@RequestMapping("/api/ai")
public class AiController {

    private final AiService aiService;

    public AiController(AiService aiService) {
        this.aiService = aiService;
    }

    /** 启用的三层 Prompt 模板 */
    @GetMapping("/templates")
    public CommonResponse<List<PromptTemplate>> templates() {
        return CommonResponse.success(aiService.listTemplates());
    }

    /** 生成财报解读简报(角色设定+数据注入+输出约束) */
    @PostMapping("/report")
    public CommonResponse<AiReport> report(@RequestBody AiReportRequest req) {
        return CommonResponse.success("简报生成成功", aiService.generateReport(req));
    }

    /** 上下文感知的追问对话 */
    @PostMapping("/chat")
    public CommonResponse<AiReport> chat(@RequestBody ChatRequest req) {
        return CommonResponse.success(aiService.chat(req));
    }

    /** 报告/对话记录(分页) */
    @GetMapping("/reports")
    public CommonResponse<PageResult<AiReport>> reports(@RequestParam Integer companyId,
                                                        @RequestParam(defaultValue = "1") int page,
                                                        @RequestParam(defaultValue = "10") int size) {
        return CommonResponse.success(aiService.listReports(companyId, page, size));
    }

    /** 报告详情 */
    @GetMapping("/reports/{id}")
    public CommonResponse<AiReport> reportDetail(@PathVariable Long id) {
        return CommonResponse.success(aiService.getReport(id));
    }
}
