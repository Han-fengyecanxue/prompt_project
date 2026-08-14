package com.fycx.mapper;

import com.fycx.entity.ValuationSnapshot;

import java.util.List;

public interface ValuationSnapshotMapper {
    int deleteByPrimaryKey(Long snapshotId);

    int insert(ValuationSnapshot row);

    int insertSelective(ValuationSnapshot row);

    ValuationSnapshot selectByPrimaryKey(Long snapshotId);

    int updateByPrimaryKeySelective(ValuationSnapshot row);

    int updateByPrimaryKey(ValuationSnapshot row);

    /** 某公司最近一条估值快照 */
    ValuationSnapshot selectLatestByCompany(Integer companyId);

    /** 某公司全部估值快照 */
    List<ValuationSnapshot> selectByCompany(Integer companyId);
}
