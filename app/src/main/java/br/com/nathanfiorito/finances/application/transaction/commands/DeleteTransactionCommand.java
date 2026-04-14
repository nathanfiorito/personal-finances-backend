package br.com.nathanfiorito.finances.application.transaction.commands;

import java.util.UUID;

public record DeleteTransactionCommand(UUID id) {}
