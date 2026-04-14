package br.com.nathanfiorito.finances.application.telegram.commands;

public record ChangeCategoryCommand(
    long chatId,
    long messageId,
    String newCategory,
    int newCategoryId
) {}
