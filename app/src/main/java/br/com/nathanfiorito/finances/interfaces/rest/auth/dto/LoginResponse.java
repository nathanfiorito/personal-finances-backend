package br.com.nathanfiorito.finances.interfaces.rest.auth.dto;

public record LoginResponse(String token, long expiresIn) {}
