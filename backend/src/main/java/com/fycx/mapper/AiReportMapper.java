package com.fycx.mapper;

import com.fycx.entity.AiReport;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface AiReportMapper {
    int deleteByPrimaryKey(Long reportId);

    int insert(AiReport row);

    AiReport selectByPrimaryKey(Long reportId);

    /** 某公司报告记录(分页, 按时间倒序) */
    List<AiReport> selectByCompany(@Param("companyId") Integer companyId,
                                   @Param("offset") int offset,
                                   @Param("limit") int limit);

    long countByCompany(Integer companyId);
}
