-- ============================================================
-- 基于Prompt工程的上市公司财报解读与行业对标系统
-- 数据库 Schema (MySQL 5.7+)
-- 库名: 财报分析系统
-- 说明: 幂等脚本, 可重复执行(会先删除旧表)
-- ============================================================

CREATE DATABASE IF NOT EXISTS `财报分析系统` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `财报分析系统`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `解读报告`;
DROP TABLE IF EXISTS `财务原始数据`;
DROP TABLE IF EXISTS `财务指标`;
DROP TABLE IF EXISTS `行业对标`;
DROP TABLE IF EXISTS `估值快照`;
DROP TABLE IF EXISTS `上市公司`;
DROP TABLE IF EXISTS `报表项目`;
DROP TABLE IF EXISTS `提示词模板`;
DROP TABLE IF EXISTS `行业分类`;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- 行业分类
-- ------------------------------------------------------------
CREATE TABLE `行业分类` (
  `行业ID` int(11) NOT NULL AUTO_INCREMENT,
  `行业代码` varchar(20) NOT NULL COMMENT '证监会行业门类代码, 如 C39',
  `行业名称` varchar(100) NOT NULL,
  `上级行业ID` int(11) NOT NULL DEFAULT '0' COMMENT '0表示顶级',
  `层级` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`行业ID`),
  UNIQUE KEY `行业代码` (`行业代码`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行业分类';

-- ------------------------------------------------------------
-- 上市公司
-- ------------------------------------------------------------
CREATE TABLE `上市公司` (
  `公司ID` int(11) NOT NULL AUTO_INCREMENT,
  `股票代码` varchar(10) NOT NULL,
  `股票简称` varchar(50) NOT NULL,
  `公司全称` varchar(200) DEFAULT NULL,
  `交易所` char(2) NOT NULL COMMENT 'SH或SZ',
  `行业ID` int(11) DEFAULT NULL,
  `上市日期` date DEFAULT NULL,
  `状态` tinyint(4) NOT NULL DEFAULT '1' COMMENT '1-正常 0-退市',
  PRIMARY KEY (`公司ID`),
  UNIQUE KEY `股票代码` (`股票代码`),
  KEY `行业ID` (`行业ID`),
  CONSTRAINT `上市公司_ibfk_1` FOREIGN KEY (`行业ID`) REFERENCES `行业分类` (`行业ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='上市公司';

-- ------------------------------------------------------------
-- 报表项目(财报原始数据字典)
-- ------------------------------------------------------------
CREATE TABLE `报表项目` (
  `项目ID` int(11) NOT NULL AUTO_INCREMENT,
  `项目编码` varchar(50) NOT NULL COMMENT '如 operating_revenue',
  `项目名称` varchar(100) NOT NULL COMMENT '如 营业收入',
  `所属报表` varchar(20) NOT NULL COMMENT '利润表/资产负债表/现金流量表',
  `单位` varchar(10) DEFAULT '元',
  `显示顺序` int(11) DEFAULT '0',
  PRIMARY KEY (`项目ID`),
  UNIQUE KEY `项目编码` (`项目编码`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报表项目';

-- ------------------------------------------------------------
-- 财务原始数据
-- ------------------------------------------------------------
CREATE TABLE `财务原始数据` (
  `数据ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `公司ID` int(11) NOT NULL,
  `财年` smallint(6) NOT NULL,
  `报告期` varchar(10) NOT NULL DEFAULT '年报',
  `项目ID` int(11) NOT NULL,
  `金额` decimal(20,2) NOT NULL,
  `数据来源` varchar(100) DEFAULT NULL,
  `入库时间` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`数据ID`),
  UNIQUE KEY `公司ID` (`公司ID`,`财年`,`报告期`,`项目ID`),
  KEY `项目ID` (`项目ID`),
  CONSTRAINT `财务原始数据_ibfk_1` FOREIGN KEY (`公司ID`) REFERENCES `上市公司` (`公司ID`),
  CONSTRAINT `财务原始数据_ibfk_2` FOREIGN KEY (`项目ID`) REFERENCES `报表项目` (`项目ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务原始数据';

-- ------------------------------------------------------------
-- 财务指标(计算引擎产出的标准化指标)
-- ------------------------------------------------------------
CREATE TABLE `财务指标` (
  `指标ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `公司ID` int(11) NOT NULL,
  `财年` smallint(6) NOT NULL,
  `报告期` varchar(10) NOT NULL DEFAULT '年报',
  `指标编码` varchar(50) NOT NULL COMMENT '如 roe',
  `指标值` decimal(12,4) NOT NULL,
  `单位` varchar(10) DEFAULT '%',
  `计算时间` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`指标ID`),
  UNIQUE KEY `公司ID` (`公司ID`,`财年`,`报告期`,`指标编码`),
  CONSTRAINT `财务指标_ibfk_1` FOREIGN KEY (`公司ID`) REFERENCES `上市公司` (`公司ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务指标';

-- ------------------------------------------------------------
-- 行业对标(行业统计基准: 均值/中位数/标准差/P25/P75)
-- ------------------------------------------------------------
CREATE TABLE `行业对标` (
  `对标ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `行业ID` int(11) NOT NULL,
  `财年` smallint(6) NOT NULL,
  `报告期` varchar(10) NOT NULL DEFAULT '年报',
  `指标编码` varchar(50) NOT NULL,
  `平均值` decimal(12,4) DEFAULT NULL,
  `中位数` decimal(12,4) DEFAULT NULL,
  `标准差` decimal(12,4) DEFAULT NULL,
  `P25` decimal(12,4) DEFAULT NULL,
  `P75` decimal(12,4) DEFAULT NULL,
  `公司数量` int(11) NOT NULL,
  PRIMARY KEY (`对标ID`),
  UNIQUE KEY `行业ID` (`行业ID`,`财年`,`报告期`,`指标编码`),
  CONSTRAINT `行业对标_ibfk_1` FOREIGN KEY (`行业ID`) REFERENCES `行业分类` (`行业ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行业对标';

-- ------------------------------------------------------------
-- 提示词模板(三层Prompt工程: 角色设定/数据注入/输出约束)
-- ------------------------------------------------------------
CREATE TABLE `提示词模板` (
  `模板ID` int(11) NOT NULL AUTO_INCREMENT,
  `模板类型` varchar(30) NOT NULL COMMENT '角色设定/数据注入/输出约束',
  `模板内容` text NOT NULL,
  `版本号` varchar(20) DEFAULT '1.0',
  `是否启用` tinyint(4) DEFAULT '1',
  PRIMARY KEY (`模板ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提示词模板';

-- ------------------------------------------------------------
-- 估值快照(收盘价/总市值, 用于PE/PB等估值指标)
-- ------------------------------------------------------------
CREATE TABLE `估值快照` (
  `快照ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `公司ID` int(11) NOT NULL,
  `快照日期` date NOT NULL,
  `收盘价` decimal(10,2) DEFAULT NULL,
  `总市值` decimal(20,2) DEFAULT NULL,
  PRIMARY KEY (`快照ID`),
  UNIQUE KEY `公司ID` (`公司ID`,`快照日期`),
  CONSTRAINT `估值快照_ibfk_1` FOREIGN KEY (`公司ID`) REFERENCES `上市公司` (`公司ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='估值快照';

-- ------------------------------------------------------------
-- 解读报告(AI简报/多轮对话记录)
-- ------------------------------------------------------------
CREATE TABLE `解读报告` (
  `报告ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `公司ID` int(11) NOT NULL,
  `财年` smallint(6) NOT NULL,
  `报告期` varchar(10) NOT NULL DEFAULT '年报',
  `报告类型` varchar(20) NOT NULL COMMENT 'brief-简报 chat-对话',
  `用户问题` text,
  `AI回答` mediumtext NOT NULL,
  `上下文` mediumtext COMMENT '注入Prompt的数据上下文(JSON), 便于审计模型是否捏造数据',
  `创建时间` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`报告ID`),
  KEY `公司ID` (`公司ID`),
  CONSTRAINT `解读报告_ibfk_1` FOREIGN KEY (`公司ID`) REFERENCES `上市公司` (`公司ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI解读报告/对话记录';
