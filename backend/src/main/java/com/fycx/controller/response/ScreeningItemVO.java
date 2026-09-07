package com.fycx.controller.response;

import lombok.Data;

import java.util.List;

/**
 * 筛选命中的公司
 */
@Data
public class ScreeningItemVO {
    private Integer companyId;
    private String stockCode;
    private String stockName;
    private String industryName;
    private Integer matchedCount;               // 命中条件数
    private List<ScreeningDetailVO> details;    // 各条件判定明细
}
