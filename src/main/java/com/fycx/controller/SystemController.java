package com.fycx.controller;

import com.fycx.controller.response.CommonResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 系统接口: 根路径信息页 + 健康检查
 */
@RestController
public class SystemController {

    private final DataSource dataSource;

    @Value("${spring.application.name:prompt_project}")
    private String appName;

    @Value("${ai.provider:mock}")
    private String aiProvider;

    public SystemController(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /** 根路径: 服务信息页(前端未部署时避免出现 404/报错) */
    @GetMapping(value = "/", produces = MediaType.TEXT_HTML_VALUE)
    public String index() {
        String dbStatus = checkDb() ? "✅ 正常" : "❌ 连接失败";
        return "<!DOCTYPE html>\n"
                + "<html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">\n"
                + "<title>上市公司财报解读与行业对标系统 - 后端服务</title>\n"
                + "<style>"
                + "body{font-family:'Microsoft YaHei',sans-serif;max-width:760px;margin:60px auto;padding:0 24px;color:#333;line-height:1.8}"
                + "h1{color:#1f3b63;border-bottom:3px solid #1f3b63;padding-bottom:12px}"
                + "h2{color:#1f3b63;margin-top:32px}"
                + "code{background:#f2f2f2;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace}"
                + "table{border-collapse:collapse;width:100%;margin:12px 0}"
                + "th,td{border:1px solid #ccc;padding:6px 12px;text-align:left;font-size:14px}"
                + "th{background:#deeaf6}"
                + ".badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;margin-right:8px}"
                + ".ok{background:#e6f4ea;color:#1e7e34}.warn{background:#fff3cd;color:#8a6d1d}"
                + "</style></head><body>\n"
                + "<h1>📊 上市公司财报解读与行业对标系统</h1>\n"
                + "<p><span class=\"badge ok\">后端服务运行中</span><span class=\"badge ok\">AI 模式: " + aiProvider + "</span>"
                + "<span class=\"badge " + (checkDb() ? "ok" : "warn") + "\">数据库: " + dbStatus + "</span></p>\n"
                + "<p>服务端口 8091 · 当前时间 " + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) + "</p>\n"
                + "<p>本页为后端服务占位页, 前端(Vue3)尚未部署。所有业务接口均以 <code>/api</code> 开头, 详见下方列表或 <code>docs/接口设计表.docx</code>。</p>\n"
                + "<h2>核心接口</h2>\n"
                + "<table><tr><th>方法</th><th>路径</th><th>说明</th></tr>\n"
                + "<tr><td>GET</td><td><code>/api/health</code></td><td>健康检查</td></tr>\n"
                + "<tr><td>GET</td><td><code>/api/finance/industries</code></td><td>行业列表</td></tr>\n"
                + "<tr><td>GET</td><td><code>/api/finance/companies</code></td><td>公司分页查询</td></tr>\n"
                + "<tr><td>GET</td><td><code>/api/finance/profile?companyId=17&amp;fiscalYear=2025</code></td><td>财务画像</td></tr>\n"
                + "<tr><td>GET</td><td><code>/api/finance/benchmark?companyId=17&amp;fiscalYear=2025</code></td><td>行业对标</td></tr>\n"
                + "<tr><td>POST</td><td><code>/api/finance/screening</code></td><td>多条件交叉筛选</td></tr>\n"
                + "<tr><td>POST</td><td><code>/api/ai/report</code></td><td>AI 财报解读简报</td></tr>\n"
                + "<tr><td>POST</td><td><code>/api/ai/chat</code></td><td>AI 追问对话</td></tr>\n"
                + "</table>\n"
                + "<h2>快速体验</h2>\n"
                + "<p>浏览器直接打开:</p>\n"
                + "<p><code><a href=\"/api/finance/benchmark?companyId=17&fiscalYear=2025\">/api/finance/benchmark?companyId=17&amp;fiscalYear=2025</a></code>"
                + "(贵州茅台 2025 行业对标)</p>\n"
                + "<p><code><a href=\"/api/health\">/api/health</a></code>(健康检查)</p>\n"
                + "</body></html>";
    }

    /** 健康检查 */
    @GetMapping("/api/health")
    public CommonResponse<Map<String, Object>> health() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("app", appName);
        data.put("status", "UP");
        data.put("database", checkDb() ? "UP" : "DOWN");
        data.put("aiProvider", aiProvider);
        data.put("time", LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        return CommonResponse.success(data);
    }

    private boolean checkDb() {
        try (Connection conn = dataSource.getConnection()) {
            return conn.isValid(3);
        } catch (Exception e) {
            return false;
        }
    }
}
