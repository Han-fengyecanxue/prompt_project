package com.fycx.common;

public enum ErrorCodeEnums {

    // ========== 用户/管理员管理 ==========
    USER_EXIST("USER_EXIST", "用户已存在"),
    USER_NOT_EXIST("USER_NOT_EXIST", "用户不存在"),
    ADMIN_EXIST("ADMIN_EXIST", "管理员已存在"),
    ADMIN_NOT_EXIST("ADMIN_NOT_EXIST", "管理员不存在"),
    PASSWORD_ERROR("PASSWORD_ERROR", "密码错误"),
    INVALID_AMOUNT("INVALID_AMOUNT", "金额无效"),
    INSUFFICIENT_BALANCE("INSUFFICIENT_BALANCE", "余额不足"),

    // ========== 财报分析系统专用错误码 ==========
    COMPANY_NOT_EXIST("COMPANY_NOT_EXIST", "公司不存在"),
    DATA_NOT_FOUND("DATA_NOT_FOUND", "未找到财务数据"),
    AI_SERVICE_ERROR("AI_SERVICE_ERROR", "AI 服务异常"),
    INVALID_YEAR("INVALID_YEAR", "无效年份"),
    REPORT_TYPE_ERROR("REPORT_TYPE_ERROR", "报告期类型错误"),
    INDICATOR_NOT_FOUND("INDICATOR_NOT_FOUND", "指标未找到"),
    BENCHMARK_NOT_FOUND("BENCHMARK_NOT_FOUND", "行业对标数据未找到"),

    // ========== 通用/附加 ==========
    INVALID_PARAM("INVALID_PARAM", "参数无效"),
    SCREENING_NO_CONDITION("SCREENING_NO_CONDITION", "筛选条件不能为空"),
    LLM_CALL_FAILED("LLM_CALL_FAILED", "大模型调用失败"),
    TEMPLATE_NOT_FOUND("TEMPLATE_NOT_FOUND", "提示词模板未找到"),
    NO_INDICATOR_DATA("NO_INDICATOR_DATA", "该公司该年度暂无指标数据，请先执行指标计算");

    private String code;
    private String desc;

    ErrorCodeEnums(String code, String desc) {
        this.code = code;
        this.desc = desc;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getDesc() {
        return desc;
    }

    public void setDesc(String desc) {
        this.desc = desc;
    }
}