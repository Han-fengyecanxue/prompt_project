package com.fycx.common;

/**
 * 自定义业务异常，支持错误码和错误信息
 */
public class HandleException extends RuntimeException {

    private String errorCode;   // 错误码
    private String errorMsg;    // 错误描述

    // ========== 构造方法 ==========

    public HandleException() {
        super();
    }

    public HandleException(String message) {
        super(message);
        this.errorMsg = message;
    }

    public HandleException(ErrorCodeEnums e) {
        super(e.getDesc());
        this.errorCode = e.getCode();
        this.errorMsg = e.getDesc();
    }

    public HandleException(String errorCode, String errorMsg) {
        super(errorMsg);
        this.errorCode = errorCode;
        this.errorMsg = errorMsg;
    }

    public HandleException(String message, String errorCode, String errorMsg) {
        super(message);
        this.errorCode = errorCode;
        this.errorMsg = errorMsg;
    }

    public HandleException(String message, Throwable cause, String errorCode, String errorMsg) {
        super(message, cause);
        this.errorCode = errorCode;
        this.errorMsg = errorMsg;
    }

    public HandleException(Throwable cause, String errorCode, String errorMsg) {
        super(cause);
        this.errorCode = errorCode;
        this.errorMsg = errorMsg;
    }

    public HandleException(String message, Throwable cause, boolean enableSuppression,
                           boolean writableStackTrace, String errorCode, String errorMsg) {
        super(message, cause, enableSuppression, writableStackTrace);
        this.errorCode = errorCode;
        this.errorMsg = errorMsg;
    }

    // ========== Getter & Setter ==========

    public String getErrorCode() {
        return errorCode;
    }

    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }

    public String getErrorMsg() {
        return errorMsg;
    }

    public void setErrorMsg(String errorMsg) {
        this.errorMsg = errorMsg;
    }

    @Override
    public String toString() {
        return "HandleException{" +
                "errorCode='" + errorCode + '\'' +
                ", errorMsg='" + errorMsg + '\'' +
                '}';
    }
}