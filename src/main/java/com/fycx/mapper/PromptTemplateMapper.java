package com.fycx.mapper;

import com.fycx.entity.PromptTemplate;

import java.util.List;

public interface PromptTemplateMapper {
    int deleteByPrimaryKey(Integer templateId);

    int insert(PromptTemplate row);

    int insertSelective(PromptTemplate row);

    PromptTemplate selectByPrimaryKey(Integer templateId);

    int updateByPrimaryKeySelective(PromptTemplate row);

    int updateByPrimaryKeyWithBLOBs(PromptTemplate row);

    int updateByPrimaryKey(PromptTemplate row);

    /** 全部启用的模板 */
    List<PromptTemplate> selectEnabled();
}
