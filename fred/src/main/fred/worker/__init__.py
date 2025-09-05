from fred.maturity import Maturity, MaturityLevel


module_maturity = Maturity(
    level=MaturityLevel.ALPHA,
    reference=__name__,
    message=(
        "Fred-Worker implementation is in early development "
        "and therefore currently with incomplete and unstable features."
    )
)