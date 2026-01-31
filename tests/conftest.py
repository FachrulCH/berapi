# Import pytest hooks from the example file
# This allows pytest to discover and use the hooks for pytest-html integration
from tests.test_pytest_html_example import (
    pytest_runtest_setup,
    pytest_runtest_makereport,
)
