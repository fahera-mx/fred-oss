
class ComponentInterface:
    
    def __or__(self, other: 'ComponentInterface') -> 'ComponentInterface':
        # union: d1 | d2 | d3  (build a group)
        # allow Node | Group and Group | Node chaining
        from fred.edag.comp._group import Group
        from fred.edag.comp._node import Node

        match self, other:
            case Node(), Node():
                return Group(nodes=[self, other])
            case Node(), Group():
                return Group(nodes=[self, *other.nodes])
            case Group(), Node():
                return Group(nodes=[*self.nodes, other])
            case Group(), Group():
                return Group(nodes=[*self.nodes, *other.nodes])
            case _:
                raise TypeError("| expects Node or Group")
