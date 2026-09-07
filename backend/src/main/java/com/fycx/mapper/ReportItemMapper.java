package com.fycx.mapper;

import com.fycx.entity.ReportItem;

import java.util.List;

public interface ReportItemMapper {
    int deleteByPrimaryKey(Integer itemId);

    int insert(ReportItem row);

    int insertSelective(ReportItem row);

    ReportItem selectByPrimaryKey(Integer itemId);

    int updateByPrimaryKeySelective(ReportItem row);

    int updateByPrimaryKey(ReportItem row);

    /** 全部报表项目 */
    List<ReportItem> selectAll();
}
