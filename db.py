from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, ForeignKey

from settings import settings

engine = create_engine(settings["DB_STRING"])
meta = MetaData()

tasks = Table(
    "tasks",
    meta,
    Column("id", Integer, primary_key=True),
    Column("text", String, nullable=False),
    Column("is_done", Boolean, nullable=False, default=False),
    Column("parent_id", ForeignKey("tasks.id"), nullable=True),
    Column("group_id", ForeignKey("groups.id"), nullable=True),
)

groups = Table(
    "groups",
    meta,
    Column("id", Integer, primary_key=True),
    Column("group_name", String, nullable=False),
)


def init_db():
    with engine.connect():
        meta.create_all(engine)

