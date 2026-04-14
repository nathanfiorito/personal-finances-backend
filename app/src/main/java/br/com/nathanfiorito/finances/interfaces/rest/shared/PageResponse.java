package br.com.nathanfiorito.finances.interfaces.rest.shared;

import br.com.nathanfiorito.finances.domain.shared.PageResult;

import java.util.List;
import java.util.function.Function;

public record PageResponse<T>(
    List<T> items,
    int total,
    int page,
    int pageSize
) {
    public static <S, T> PageResponse<T> from(PageResult<S> result,
                                               Function<S, T> mapper,
                                               int page,
                                               int pageSize) {
        return new PageResponse<>(
            result.items().stream().map(mapper).toList(),
            result.total(),
            page,
            pageSize
        );
    }
}
