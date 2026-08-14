package com.fycx.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.resource.NoResourceFoundException;
import com.fycx.controller.response.CommonResponse;

/**
 * 全局异常处理器: 统一返回 CommonResponse
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** 业务异常 */
    @ExceptionHandler(HandleException.class)
    public CommonResponse<Void> handleBusiness(HandleException e) {
        log.warn("业务异常: {}", e.getErrorMsg());
        return CommonResponse.error(e.getErrorCode() == null ? "BUSINESS_ERROR" : e.getErrorCode(),
                e.getErrorMsg() == null ? "业务处理失败" : e.getErrorMsg());
    }

    /** 参数异常 */
    @ExceptionHandler(IllegalArgumentException.class)
    public CommonResponse<Void> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("参数异常: {}", e.getMessage());
        return CommonResponse.error(ErrorCodeEnums.INVALID_PARAM.getCode(), e.getMessage());
    }

    /** 404: 请求的路径/静态资源不存在(如未部署前端时访问根路径) */
    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<CommonResponse<Void>> handleNoResource(NoResourceFoundException e) {
        log.warn("资源不存在: {}", e.getResourcePath());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(CommonResponse.error("NOT_FOUND", "接口或资源不存在: " + e.getResourcePath()
                        + " (前端尚未部署, 后端接口前缀为 /api)"));
    }

    /** 兜底异常 */
    @ExceptionHandler(Exception.class)
    public CommonResponse<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return CommonResponse.error("SYSTEM_ERROR", "系统内部错误: " + e.getMessage());
    }
}
