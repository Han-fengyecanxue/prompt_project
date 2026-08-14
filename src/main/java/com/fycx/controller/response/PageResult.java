package com.fycx.controller.response;

import lombok.Data;

import java.util.List;

/**
 * 通用分页结果
 */
@Data
public class PageResult<T> {
    private long total;
    private int page;
    private int size;
    private List<T> list;

    public PageResult() {
    }

    public PageResult(long total, int page, int size, List<T> list) {
        this.total = total;
        this.page = page;
        this.size = size;
        this.list = list;
    }
}
