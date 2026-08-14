package com.fycx.mapper;

import com.fycx.entity.IndustryCategory;
import com.fycx.controller.response.IndustryVO;

import java.util.List;

public interface IndustryCategoryMapper {
    int deleteByPrimaryKey(Integer industryId);

    int insert(IndustryCategory row);

    int insertSelective(IndustryCategory row);

    IndustryCategory selectByPrimaryKey(Integer industryId);

    int updateByPrimaryKeySelective(IndustryCategory row);

    int updateByPrimaryKey(IndustryCategory row);

    // ========== 自定义查询 ==========

    /** 全部行业(含公司数量) */
    List<IndustryVO> selectAllWithCount();
}
