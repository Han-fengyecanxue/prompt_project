package com.fycx.mapper;

import com.fycx.entity.FinancialData;
import com.fycx.controller.response.RawItemVO;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface FinancialDataMapper {
    int deleteByPrimaryKey(Long dataId);

    int insert(FinancialData row);

    int insertSelective(FinancialData row);

    FinancialData selectByPrimaryKey(Long dataId);

    int updateByPrimaryKeySelective(FinancialData row);

    int updateByPrimaryKey(FinancialData row);

    // ========== 自定义查询 ==========

    /** 某公司某年度原始项目明细(带编码/名称/单位) */
    List<RawItemVO> selectItemsByCompanyYear(@Param("companyId") Integer companyId,
                                             @Param("fiscalYear") Integer fiscalYear,
                                             @Param("reportPeriod") String reportPeriod);

    /** 某公司全部年度原始数据(计算引擎用) */
    List<FinancialData> selectByCompanyAllYears(Integer companyId);

    /** 按公司+年度+报告期删除 */
    int deleteByCompanyYear(@Param("companyId") Integer companyId,
                            @Param("fiscalYear") Integer fiscalYear,
                            @Param("reportPeriod") String reportPeriod);
}
