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

-- ============================================================
-- 基础字典数据 (与真实财报数据配套, 3行业/24家上市公司/22个报表科目/3条Prompt模板)
-- 说明: 字典部分为真实定义(公司/行业/科目均为真实主体), 模拟的仅是财务数字;
--       模拟财务数字已由 03_real_data.sql 中的真实数据取代。
-- ============================================================
-- 行业分类
INSERT INTO `行业分类` (`行业ID`,`行业代码`,`行业名称`,`上级行业ID`,`层级`) VALUES (1,'C39','计算机、通信和其他电子设备制造业',0,1);
INSERT INTO `行业分类` (`行业ID`,`行业代码`,`行业名称`,`上级行业ID`,`层级`) VALUES (2,'C27','医药制造业',0,1);
INSERT INTO `行业分类` (`行业ID`,`行业代码`,`行业名称`,`上级行业ID`,`层级`) VALUES (3,'C15','酒、饮料和精制茶制造业',0,1);

-- 报表项目
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (1,'operating_revenue','营业收入','利润表','元',1);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (2,'operating_cost','营业成本','利润表','元',2);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (3,'gross_profit','营业利润','利润表','元',5);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (4,'net_profit','净利润','利润表','元',10);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (5,'net_profit_parent','归属于上市公司股东的净利润','利润表','元',11);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (6,'net_profit_parent_deducted','扣除非经常性损益的净利润','利润表','元',12);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (7,'eps_basic','基本每股收益','利润表','元/股',20);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (8,'monetary_funds','货币资金','资产负债表','元',1);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (9,'trading_financial_assets','交易性金融资产','资产负债表','元',2);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (10,'notes_receivable','应收票据','资产负债表','元',5);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (11,'accounts_receivable','应收账款','资产负债表','元',6);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (12,'inventory','存货','资产负债表','元',10);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (13,'total_assets','总资产','资产负债表','元',50);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (14,'short_term_borrowings','短期借款','资产负债表','元',60);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (15,'accounts_payable','应付账款','资产负债表','元',65);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (16,'total_liabilities','总负债','资产负债表','元',90);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (17,'total_equity','股东权益合计','资产负债表','元',95);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (18,'operating_cashflow','经营活动现金流量净额','现金流量表','元',10);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (19,'investing_cashflow','投资活动现金流量净额','现金流量表','元',20);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (20,'financing_cashflow','筹资活动现金流量净额','现金流量表','元',30);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (21,'current_assets_total','流动资产合计','资产负债表','元',40);
INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (22,'current_liabilities_total','流动负债合计','资产负债表','元',85);

-- 上市公司
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (1,'300308','中际旭创','中际旭创股份有限公司','SZ',1,'2012-04-10',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (2,'300502','新易盛','成都新易盛通信技术股份有限公司','SZ',1,'2016-03-03',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (3,'300394','天孚通信','苏州天孚光通信股份有限公司','SZ',1,'2015-02-17',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (4,'002475','立讯精密','立讯精密工业股份有限公司','SZ',1,'2010-09-15',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (5,'601138','工业富联','富士康工业互联网股份有限公司','SH',1,'2018-06-08',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (6,'002463','沪电股份','沪士电子股份有限公司','SZ',1,'2010-08-18',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (7,'002916','深南电路','深南电路股份有限公司','SZ',1,'2017-12-13',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (8,'600183','生益科技','广东生益科技股份有限公司','SH',1,'1998-10-28',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (9,'600276','恒瑞医药','江苏恒瑞医药股份有限公司','SH',2,'2000-10-18',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (10,'603259','药明康德','无锡药明康德新药开发股份有限公司','SH',2,'2018-05-08',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (11,'300760','迈瑞医疗','深圳迈瑞生物医疗电子股份有限公司','SZ',2,'2018-10-16',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (12,'600436','片仔癀','漳州片仔癀药业股份有限公司','SH',2,'2003-06-16',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (13,'000538','云南白药','云南白药集团股份有限公司','SZ',2,'1993-12-15',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (14,'600196','复星医药','上海复星医药(集团)股份有限公司','SH',2,'1998-08-07',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (15,'300122','智飞生物','重庆智飞生物制品股份有限公司','SZ',2,'2010-09-28',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (16,'000661','长春高新','长春高新技术产业(集团)股份有限公司','SZ',2,'1996-12-18',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (17,'600519','贵州茅台','贵州茅台酒股份有限公司','SH',3,'2001-08-27',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (18,'000858','五粮液','宜宾五粮液股份有限公司','SZ',3,'1998-04-27',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (19,'000568','泸州老窖','泸州老窖股份有限公司','SZ',3,'1994-05-09',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (20,'600809','山西汾酒','山西杏花村汾酒厂股份有限公司','SH',3,'1994-01-06',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (21,'002304','洋河股份','江苏洋河酒厂股份有限公司','SZ',3,'2009-11-06',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (22,'000596','古井贡酒','安徽古井贡酒股份有限公司','SZ',3,'1996-09-27',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (23,'603369','今世缘','江苏今世缘酒业股份有限公司','SH',3,'2014-07-03',1);
INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (24,'600600','青岛啤酒','青岛啤酒股份有限公司','SH',3,'1993-08-27',1);

-- 提示词模板(三层Prompt工程)
INSERT INTO `提示词模板` (`模板ID`,`模板类型`,`模板内容`,`版本号`,`是否启用`) VALUES (1,'角色设定','你是一位资深的上司公司财务分析师，拥有 CFA 资质与 10 年以上 A 股财报分析经验，擅长通过财务指标对上市公司进行客观诊断，并以通俗易懂的语言向普通投资者解释专业结论。你的分析风格：客观、严谨、克制，不夸大、不唱多、不唱空，结论必须有数据支撑。','1.0',1);
INSERT INTO `提示词模板` (`模板ID`,`模板类型`,`模板内容`,`版本号`,`是否启用`) VALUES (2,'数据注入','以下是由系统精确计算出的【该公司】{fiscalYear}年财务指标与行业对标数据（JSON 格式），这是本次分析唯一可信的数据来源：
{data_json}
行业对标口径：行业均值/中位数/P25/P75 基于同行业上市公司同一年度数据计算；百分位排名表示该公司指标值在行业内所处位置（0-100，越高表示相对越优）。','1.0',1);
INSERT INTO `提示词模板` (`模板ID`,`模板类型`,`模板内容`,`版本号`,`是否启用`) VALUES (3,'输出约束','请严格按照以下要求输出解读报告：
1. 只能使用【数据注入】中提供的数据，严禁编造、推断或补充任何数据注入中不存在的数字；
2. 报告结构固定为：一、公司概览；二、盈利能力分析；三、成长性分析；四、财务风险分析；五、估值水平分析；六、综合结论与风险提示；
3. 每个章节必须引用具体指标数值与行业对标结果（如：ROE 为 25.3%，高于行业中位数 18.2%）；
4. 结论部分给出综合评级（优秀/良好/一般/偏弱）与理由；
5. 使用中文、Markdown 格式，控制在 800 字以内；
6. 如果某维度数据缺失，明确说明“该维度数据不足，无法分析”，不得猜测。','1.0',1);
