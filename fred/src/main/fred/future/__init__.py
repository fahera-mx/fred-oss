from fred.maturity import Maturity, MaturityLevel
from fred.future.impl import Future


module_maturity = Maturity(
    level=MaturityLevel.ALPHA,
    reference=__name__,
    message=(
        "Fred-Futures implementation is in early development "
        "and therefore currently with incomplete and unstable features."
    )
)
