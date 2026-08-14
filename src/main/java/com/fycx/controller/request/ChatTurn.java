package com.fycx.controller.request;

import lombok.Data;

import java.util.List;

/**
 * AI 对话轮次
 */
@Data
public class ChatTurn {
    private String role;      // user / assistant
    private String content;
}
