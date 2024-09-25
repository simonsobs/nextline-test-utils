import nextline_test_utils


def test_version() -> None:
    '''Confirm that the version string is attached to the module'''
    nextline_test_utils.__version__
