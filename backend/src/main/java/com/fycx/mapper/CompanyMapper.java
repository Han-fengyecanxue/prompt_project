package com.fycx.mapper;

import com.fycx.entity.Company;
import com.fycx.controller.response.CompanyVO;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface CompanyMapper {
    int deleteByPrimaryKey(Integer companyId);

    int insert(Company row);

    int insertSelective(Company row);

    Company selectByPrimaryKey(Integer companyId);

    int updateByPrimaryKeySelective(Company row);

    int updateByPrimaryKey(Company row);

    // ========== 自定义查询 ==========

    /** 分页条件查询(含行业名称) */
    List<CompanyVO> selectByCondition(@Param("keyword") String keyword,
                                      @Param("industryId") Integer industryId,
                                      @Param("status") Integer status,
                                      @Param("offset") int offset,
                                      @Param("limit") int limit);

    /** 条件计数 */
    long countByCondition(@Param("keyword") String keyword,
                          @Param("industryId") Integer industryId,
                          @Param("status") Integer status);

    /** 按主键查询(含行业名称) */
    CompanyVO selectVOByPrimaryKey(Integer companyId);

    /** 全部公司(含行业名称) */
    List<CompanyVO> selectAllVO();
}
