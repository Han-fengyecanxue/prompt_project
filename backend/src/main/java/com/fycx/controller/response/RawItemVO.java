package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 财报原始项目(带编码与名称)
 */
@Data
public class RawItemVO {
    private String itemCode;
    private String itemName;
    private String reportType;
    private String unit;
    private BigDecimal amount;
}
