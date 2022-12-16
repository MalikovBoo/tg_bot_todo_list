from dataclasses import dataclass


@dataclass
class Group:
    id: int
    group_name: str = ""

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.id}. {self.text}"
