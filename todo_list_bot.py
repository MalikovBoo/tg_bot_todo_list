from aiogram import Bot, Dispatcher, types
from aiogram.utils.callback_data import CallbackData

from settings import settings
from task import Task
from group import Group
from task_repository import TaskRepository
from group_repository import GroupRepository


import typing

bot = Bot(token=settings["TELEGRAM_TOKEN"])
dispatcher = Dispatcher(bot)
clear_cb = CallbackData("clear", "action")

tasks = []

_repository = TaskRepository()
_grepository = GroupRepository()


def _task_dto_to_string(task: Task) -> str:
    status_char = "\u2705" if task.is_done else "\u274c"
    parent = "" if task.parent_id is None else "    "
    group = "" if task.group_id is None else "Группа: "+str(task.group_id)
    return f"{parent}{task.id}: {task.text} | {status_char} {group}"


def _group_dto_to_string(group: Group) -> str:
    return f"{group.id}: {group.group_name}"


def _get_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton(
            "Удалить все!", callback_data=clear_cb.new(action="all")
        ),
        types.InlineKeyboardButton(
            "Только завершенные", callback_data=clear_cb.new(action="completed")
        ),
    )


@dispatcher.message_handler(commands=["help"])
async def create_task(message: types.Message):
    text = "Список команд: \n\n" \
           "/task *текст задачи*\n - добавить новую задачу \n\n" \
           "/subtask *№ родительской задачи* *текст подзадачи*\n - добавить новую подзадачу \n\n" \
           "/add_group *название группы* \n - добавить новую группу для задач \n\n"\
           "/add_to_group *№ группы* *№ задачи* \n - добавить существующую задачу в существующую группу \n\n"\
           "/list\n - вывести список всех текущих задач \n\n" \
           "/group_list\n - вывести список всех групп \n\n" \
           "/tasks_in_group *№ группы*\n - вывести список всех задач в группе с указанным номером \n\n" \
           "/find *искомая фраза*\n - вывести список задач, в который есть искомая фраза \n\n" \
           "/done *номера задач через пробел*\n - отметить задачи как выполненные \n\n" \
           "/reopen *номера задач через пробел*\n - отменить выполненность задач \n\n" \
           "/clear\n - очистить список задач (дальше можно выбрать тип удаления)"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["task"])
async def create_task(message: types.Message):
    task_num = _repository.add_task(message.get_args())
    await message.reply(f"Добавлена новая задача. Её номер - {task_num}")


@dispatcher.message_handler(commands=["subtask"])
async def create_subtask(message: types.Message):
    try:
        task_num = _repository.add_subtask(parent_id=int(message.get_args().split()[0]), text=" ".join(message.get_args().split()[1:]))
        if task_num != -1:
            text = f"Добавлена новая подзадача. Её номер - {task_num} "
        else:
            text = "Возможен только один уровень вложенности!"
    except:
        text = "Неправильный номер задачи"
    await message.reply(text)


@dispatcher.message_handler(commands=["add_group"])
async def create_group(message: types.Message):
    group_num = _grepository.add_group(message.get_args())
    await message.reply(f"Добавлена новая группа. Её номер - {group_num}")


@dispatcher.message_handler(commands=["add_to_group"])
async def add_to_group(message: types.Message):
    try:
        group_id = message.get_args().split(" ")[0]
        task_id = message.get_args().split(" ")[1]
        text = _repository.add_to_group(int(group_id), int(task_id))
    except:
        text = "Произошла ошибка при добавлении"

    await message.reply(text)


@dispatcher.message_handler(commands=["list"])
async def get_list(message: types.Message):
    tasks = _repository.get_list()
    if tasks:
        text = "\n".join([_task_dto_to_string(res) for res in tasks])
    else:
        text = "У вас нет задач!"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["group_list"])
async def get_group_list(message: types.Message):
    groups = _grepository.get_group_list()
    if groups:
        text = "\n".join([_group_dto_to_string(res) for res in groups])
    else:
        text = "У вас нет групп!"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["tasks_in_group"])
async def get_group_task_list(message: types.Message):
    tasks = _repository.get_task_list_in_group(message.get_args())
    if tasks:
        text = "\n".join([_task_dto_to_string(res) for res in tasks])
    else:
        text = "У вас нет задач c такой группой!"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["find"])
async def get_ilike_list(message: types.Message):
    tasks = _repository.get_ilike_list(message.get_args())
    if tasks:
        text = "\n".join([_task_dto_to_string(res) for res in tasks])
    else:
        text = "Задач с таким текстом не найдено!"
    await bot.send_message(message.chat.id, text)


@dispatcher.message_handler(commands=["done"])
async def finish_task(message: types.Message):
    try:
        task_ids = [int(id_) for id_ in message.get_args().split(" ")]
        _repository.finish_tasks(task_ids)
        text = f"Завершенные задачи: {task_ids}"
    except ValueError as e:
        text = "Неправильный номер задачи"

    await message.reply(text)


@dispatcher.message_handler(commands=["reopen"])
async def reopen_tasks(message: types.Message):
    try:
        task_ids = [int(id_) for id_ in message.get_args().split(" ")]
        _repository.reopen_tasks(task_ids)
        text = f"Переоткрытые задачи: {task_ids}"
    except ValueError as e:
        text = "Неправильный номер задачи"

    await message.reply(text)


@dispatcher.message_handler(commands=["clear"])
async def clear(message: types.Message):
    await message.reply("Вы хотите удалить ваши задачи?", reply_markup=_get_keyboard())


@dispatcher.callback_query_handler(clear_cb.filter(action=["all", "completed"]))
async def callback_clear_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    await query.answer()
    callback_data_action = callback_data["action"]

    if callback_data_action == "all":
        _repository.clear()
    else:
        _repository.clear(is_done=True)

    await bot.edit_message_text(
        f"Задачи удалены! ",
        query.from_user.id,
        query.message.message_id,
    )
