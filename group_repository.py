from db import groups, engine
from group import Group

from typing import List


class GroupRepository:
    def add_group(self, text: str) -> int:
        query = groups.insert().values(group_name=text)
        result = ""
        with engine.connect() as conn:
            result = conn.execute(query).inserted_primary_key[0]
        return result

    def get_group_list(self) -> List[Group]:
        query = groups.select()
        result = []
        with engine.connect() as conn:
            result = [
                Group(id=id, group_name=group_name)
                for id, group_name in conn.execute(query.order_by(groups.c.id))
            ]
        return result

  