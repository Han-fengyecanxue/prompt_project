package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 估值快照
 */
@Data
public class ValuationVO {
    private Date snapshotDate;
    private BigDecimal closePrice;
    private BigDecimal marketCap;
}
