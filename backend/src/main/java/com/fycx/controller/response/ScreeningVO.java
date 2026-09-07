package com.fycx.controller.response;

import lombok.Data;

import java.util.List;

/**
 * 多条件交叉筛选结果
 */
@Data
public class ScreeningVO {
    private Integer total;                       // 命中公司数
    private Integer conditionCount;              // 条件数
    private List<ScreeningItemVO> companies;     // 命中公司
}
