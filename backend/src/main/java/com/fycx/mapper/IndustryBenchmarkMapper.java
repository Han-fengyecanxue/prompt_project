package com.fycx.mapper;

import com.fycx.entity.IndustryBenchmark;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface IndustryBenchmarkMapper {
    int deleteByPrimaryKey(Long benchmarkId);

    int insert(IndustryBenchmark row);

    int insertSelective(IndustryBenchmark row);

    IndustryBenchmark selectByPrimaryKey(Long benchmarkId);

    int updateByPrimaryKeySelective(IndustryBenchmark row);

    int updateByPrimaryKey(IndustryBenchmark row);

    // ========== 自定义查询 ==========

    /** 某行业某年度对标数据 */
    List<IndustryBenchmark> selectByIndustryYear(@Param("industryId") Integer industryId,
                                                 @Param("fiscalYear") Integer fiscalYear,
                                                 @Param("reportPeriod") String reportPeriod);

    /** 清空全部对标(重算用) */
    int deleteAll();

    /** 批量插入 */
    int insertBatch(List<IndustryBenchmark> list);
}
