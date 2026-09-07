package com.fycx.controller.response;

import com.fycx.common.ErrorCodeEnums;
import lombok.Data;

/**
 * 统一响应结构
 */
@Data
public class CommonResponse<T> {

    private String code;      // 业务码: 0 成功, 其他见 ErrorCodeEnums
    private String message;   // 提示信息
    private T data;           // 业务数据

    public CommonResponse() {
    }

    public CommonResponse(String code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> CommonResponse<T> success(T data) {
        return new CommonResponse<>("0", "success", data);
    }

    public static <T> CommonResponse<T> success(String message, T data) {
        return new CommonResponse<>("0", message, data);
    }

    public static <T> CommonResponse<T> error(String code, String message) {
        return new CommonResponse<>(code, message, null);
    }

    public static <T> CommonResponse<T> error(ErrorCodeEnums e) {
        return new CommonResponse<>(e.getCode(), e.getDesc(), null);
    }
}
