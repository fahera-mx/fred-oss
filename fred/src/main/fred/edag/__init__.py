from fred.maturity import Maturity, MaturityLevel
from fred.edag.decorator import NodeDecorator


module_maturity = Maturity(
    level=MaturityLevel.ALPHA,
    reference=__name__,
    message=(
        "Fred-eDAG implementation is in early development "
        "and therefore currently with incomplete and unstable features."
    )
)


node = NodeDecorator
