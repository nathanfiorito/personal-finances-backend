package br.com.nathanfiorito.finances.domain.shared;

import java.util.List;

public record PageResult<T>(List<T> items, int total) {}
