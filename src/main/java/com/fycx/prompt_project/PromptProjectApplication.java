package com.fycx.prompt_project;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.Banner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 上市公司财报解读与行业对标系统 启动类
 */
@SpringBootApplication(scanBasePackages = "com.fycx")
@MapperScan("com.fycx.mapper")
public class PromptProjectApplication {

    public static void main(String[] args) {
        SpringApplication application = new SpringApplication(PromptProjectApplication.class);
        application.setBannerMode(Banner.Mode.OFF);
        application.run(args);
    }
}
