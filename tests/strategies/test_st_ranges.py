import sys
from typing import Optional, TypeVar

from hypothesis import given, settings
from hypothesis import strategies as st

from nextline_test_utils import safe_compare as sc
from nextline_test_utils import safe_max
from nextline_test_utils.strategies import (
    StMinMaxValuesFactory,
    st_datetimes,
    st_graphql_ints,
    st_none_or,
    st_ranges,
)

if sys.version_info >= (3, 11):
    from typing import Generic, TypedDict
else:
    from typing_extensions import Generic, TypedDict


T = TypeVar('T')


def st_min_max_start(
    st_: StMinMaxValuesFactory[T],
) -> st.SearchStrategy[tuple[Optional[T], Optional[T]]]:
    def st_min() -> st.SearchStrategy[Optional[T]]:
        return st_none_or(st_())

    def st_max(min_value: Optional[T]) -> st.SearchStrategy[Optional[T]]:
        return st_none_or(st_(min_value=min_value))

    return st_min().flatmap(lambda min_: st.tuples(st.just(min_), st_max(min_)))


def st_min_max_end(
    st_: StMinMaxValuesFactory[T],
    min_start: Optional[T] = None,
) -> st.SearchStrategy[tuple[Optional[T], Optional[T]]]:
    def st_min() -> st.SearchStrategy[Optional[T]]:
        return st_none_or(st_(min_value=min_start))

    def st_max(min_value: Optional[T]) -> st.SearchStrategy[Optional[T]]:
        min_value = safe_max((min_value, min_start))
        return st_none_or(st_(min_value=min_value))

    return st_min().flatmap(lambda min_: st.tuples(st.just(min_), st_max(min_)))


class StRangesKwargs(TypedDict, Generic[T], total=False):
    # st_: StMinMaxValuesFactory[T]
    min_start: Optional[T]
    max_start: Optional[T]
    min_end: Optional[T]
    max_end: Optional[T]
    allow_start_none: bool
    allow_end_none: bool
    let_end_none_if_start_none: bool
    allow_equal: bool


@st.composite
def st_st_ranges_kwargs(
    draw: st.DrawFn, st_: StMinMaxValuesFactory[T] | None = None
) -> StRangesKwargs[T]:
    st_ = st_ or st.integers  # type: ignore
    kwargs = StRangesKwargs[T]()

    min_start, max_start = draw(st_min_max_start(st_=st_))  # type: ignore
    if min_start is not None:
        kwargs['min_start'] = min_start
    if max_start is not None:
        kwargs['max_start'] = max_start

    min_end, max_end = draw(st_min_max_end(st_=st_, min_start=min_start))  # type: ignore
    if min_end is not None:
        kwargs['min_end'] = min_end
    if max_end is not None:
        kwargs['max_end'] = max_end

    if draw(st.booleans()):
        kwargs['allow_start_none'] = draw(st.booleans())
    if draw(st.booleans()):
        kwargs['allow_end_none'] = draw(st.booleans())
    if draw(st.booleans()):
        kwargs['allow_equal'] = draw(st.booleans())
    if draw(st.booleans()):
        kwargs['let_end_none_if_start_none'] = draw(st.booleans())

    return kwargs


@given(st.data())
def test_st_st_ranges_kwargs(data: st.DataObject) -> None:
    st_ = data.draw(st.sampled_from([None, st_graphql_ints, st_datetimes]))
    kwargs = data.draw(st_st_ranges_kwargs(st_=st_))  # type: ignore

    min_start = kwargs.get('min_start')
    max_start = kwargs.get('max_start')
    assert sc(min_start) <= sc(max_start)

    min_end = kwargs.get('min_end')
    max_end = kwargs.get('max_end')
    assert sc(min_start) <= sc(min_end) <= sc(max_end)


@given(st.data())
@settings(max_examples=1000)
def test_st_ranges(data: st.DataObject) -> None:
    st_ = data.draw(st.sampled_from([None, st_graphql_ints, st_datetimes]))
    kwargs = data.draw(st_st_ranges_kwargs(st_=st_))  # type: ignore
    
    args = (st_,) if st_ is not None else ()

    start, end = data.draw(st_ranges(*args, **kwargs))  # type: ignore

    allow_start_none = kwargs.get('allow_start_none', True)
    if not allow_start_none:
        assert start is not None

    let_end_none_if_start_none = kwargs.get('let_end_none_if_start_none', False)
    allow_end_none = kwargs.get('allow_end_none', True)
    if start is None and let_end_none_if_start_none:
        assert end is None
    elif not allow_end_none:
        assert end is not None

    allow_equal = kwargs.get('allow_equal', True)
    if allow_equal:
        assert sc(start) <= sc(end)
    else:
        assert sc(start) < sc(end)

    min_start = kwargs.get('min_start')
    max_start = kwargs.get('max_start')
    assert sc(min_start) <= sc(start) <= sc(max_start)

    min_end = kwargs.get('min_end')
    max_end = kwargs.get('max_end')
    assert sc(min_end) <= sc(end) <= sc(max_end)
