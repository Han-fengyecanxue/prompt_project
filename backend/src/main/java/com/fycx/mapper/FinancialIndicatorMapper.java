package com.fycx.mapper;

import com.fycx.entity.FinancialIndicator;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface FinancialIndicatorMapper {
    int deleteByPrimaryKey(Long indicatorId);

    int insert(FinancialIndicator row);

    int insertSelective(FinancialIndicator row);

    FinancialIndicator selectByPrimaryKey(Long indicatorId);

    int updateByPrimaryKeySelective(FinancialIndicator row);

    int updateByPrimaryKey(FinancialIndicator row);

    // ========== 自定义查询 ==========

    /** 某公司某年度指标 */
    List<FinancialIndicator> selectByCompanyYear(@Param("companyId") Integer companyId,
                                                 @Param("fiscalYear") Integer fiscalYear,
                                                 @Param("reportPeriod") String reportPeriod);

    /** 某公司全部年度指标 */
    List<FinancialIndicator> selectByCompanyAllYears(Integer companyId);

    /** 某年度全市场指标 */
    List<FinancialIndicator> selectByYear(@Param("fiscalYear") Integer fiscalYear,
                                          @Param("reportPeriod") String reportPeriod);

    /** 某行业某年度指标(联表上市公司) */
    List<FinancialIndicator> selectByIndustryYear(@Param("industryId") Integer industryId,
                                                  @Param("fiscalYear") Integer fiscalYear,
                                                  @Param("reportPeriod") String reportPeriod);

    /** 清空全部指标(重算用) */
    int deleteAll();

    /** 批量插入 */
    int insertBatch(List<FinancialIndicator> list);
}
