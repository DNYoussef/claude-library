import warnings


warnings.filterwarnings(
    "ignore",
    message=(
        "datetime\\.datetime\\.utcnow\\(\\) is deprecated and scheduled for "
        "removal in a future version\\."
    ),
    category=DeprecationWarning,
    module="pytest_benchmark.utils",
)
