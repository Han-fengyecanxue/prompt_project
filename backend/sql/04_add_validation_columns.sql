-- ============================================================
-- 为已有库的 ai_report 表补充"数值校验结果"两列 (P0-2)
-- 说明: 仅需对"已存在的老库"执行一次; 全新由 01_schema.sql 建的表无需此步。
-- 兼容旧版本 MySQL (普通 ADD COLUMN, 8.0.30 以下不支持 IF NOT EXISTS)
-- 注意: 本脚本只执行一次即可; 若重复执行会报"列已存在"的重复列错误, 可忽略。
-- ============================================================
USE `financial_analysis`;

ALTER TABLE `ai_report`
  ADD COLUMN `numeric_accuracy` decimal(5,2) DEFAULT NULL COMMENT '数值引用准确率(%): 报告可溯源数字占比' AFTER `context_json`,
  ADD COLUMN `suspicious_count` int(11) DEFAULT NULL COMMENT '可疑(疑似幻觉)数字数量' AFTER `numeric_accuracy`;

-- 验证: 应能看到新增的两列
SHOW COLUMNS FROM `ai_report` LIKE 'numeric_accuracy';
SHOW COLUMNS FROM `ai_report` LIKE 'suspicious_count';