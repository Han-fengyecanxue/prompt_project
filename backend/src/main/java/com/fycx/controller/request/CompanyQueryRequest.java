package com.fycx.controller.request;

import lombok.Data;

/**
 * 公司查询请求(分页 + 关键字 + 行业过滤)
 */
@Data
public class CompanyQueryRequest {
    private String keyword;       // 股票代码/简称/全称 模糊匹配
    private Integer industryId;
    private Integer status = 1;
    private Integer page = 1;
    private Integer size = 10;
}
