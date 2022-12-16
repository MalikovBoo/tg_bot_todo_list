from db import tasks, groups, engine
from task import Task
from group import Group

from typing import List


class TaskRepository:
    def add_task(self, text: str) -> int:
        query = tasks.insert().values(text=text)
        result = ""
        with engine.connect() as conn:
            result = conn.execute(query).inserted_primary_key[0]
        return result

    def add_subtask(self, text: str, parent_id: int) -> int:
        parent_query = tasks.select().filter(tasks.c.id==parent_id, tasks.c.parent_id==None)
        parent = ""
        with engine.connect() as conn:
            parent = conn.execute(parent_query)
            if parent.rowcount:
                parent_group_id = ""
                for row in parent:
                    parent_group_id = int(row["group_id"])
                query = tasks.insert().values(text=text, parent_id=parent_id, group_id=parent_group_id)
                result = ""
                with engine.connect() as conn:
                    result = conn.execute(query).inserted_primary_key[0]
                return result
            else:
                return -1

    def add_to_group(self, group_id: int, id: int) -> str:
        query_group = groups.select().filter(groups.c.id == group_id)
        with engine.connect() as conn:
            my_group = conn.execute(query_group)
        i = 0
        for row in my_group:
            i += 1
        if i > 0:
            query = tasks.update().where(tasks.c.id == id).values(group_id=group_id)
            with engine.connect() as conn:
                conn.execute(query)
            return "Задача добавлена в группу!"
        else:
            return "Группы с таким номером не существует."

    def get_list(self, is_done=None) -> List[Task]:
        query = tasks.select()

        if is_done is not None:
            query = query.where(is_done=is_done)

        result = []
        with engine.connect() as conn:
            result = [
                Task(id=id, text=text, is_done=is_done, parent_id=parent_id, group_id=group_id)
                for id, text, is_done, parent_id, group_id in conn.execute(query.order_by(tasks.c.id))
            ]
            result = sorted(result, key=lambda x: x.parent_id if x.parent_id is not None else x.id)
        return result

    def get_task_list_in_group(self, group_id: str) -> List[Task]:
        query = tasks.select().where(tasks.c.group_id == int(group_id))
        result = []
        with engine.connect() as conn:
            result = [
                Task(id=id, text=text, is_done=is_done, parent_id=parent_id, group_id=group_id)
                for id, text, is_done, parent_id, group_id in conn.execute(query.order_by(tasks.c.id))
            ]
            result = sorted(result, key=lambda x: x.parent_id if x.parent_id is not None else x.id)
        return result

    def get_ilike_list(self, ilike_text="") -> List[Task]:
        query = tasks.select()

        result = []
        with engine.connect() as conn:
            result = [
                Task(id=id, text=text, is_done=is_done)
                for id, text, is_done in
                conn.execute(query.filter(tasks.c.text.ilike(f"%{ilike_text}%")).order_by(tasks.c.id))
            ]

        return result

    def finish_tasks(self, ids: List[int]):
        query = tasks.update().where(tasks.c.id.in_(ids)).values(is_done=True)
        query_child = tasks.update().where(tasks.c.parent_id.in_(ids)).values(is_done=True)
        with engine.connect() as conn:
            conn.execute(query)
            conn.execute(query_child)

    def reopen_tasks(self, ids: List[int]):
        query = tasks.update().where(tasks.c.id.in_(ids)).values(is_done=False)
        query_child = tasks.update().where(tasks.c.parent_id.in_(ids)).values(is_done=False)
        with engine.connect() as conn:
            conn.execute(query)
            conn.execute(query_child)

    def clear(self, is_done=None):
        query = tasks.delete()

        if is_done is not None:
            query_parent = tasks.select().filter(tasks.c.parent_id==None).filter(tasks.c.is_done==True)
            parents = ""
            with engine.connect() as conn:
                parents = conn.execute(query_parent)
            parent_list = []
            for row in parents:
                parent_list.append(row['id'])
            query_children = query.where(tasks.c.parent_id.in_(parent_list))
            with engine.connect() as conn:
                conn.execute(query_children)
            query = query.where(tasks.c.is_done==True)

        with engine.connect() as conn:
            conn.execute(query)
