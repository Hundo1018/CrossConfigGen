import configparser
import ast
import json


def infer_type(value: str):
    """根據值的內容解析型別"""
    value = value.strip()  # 去除多餘空白
    if value.lower() in {"true", "false"}:  # 布林值
        return ast.Constant(value=value.lower() == "true")
    try:  # 整數
        return ast.Constant(value=int(value))
    except ValueError:
        pass
    try:  # 浮點數
        return ast.Constant(value=float(value))
    except ValueError:
        pass

    # 解析逗號分隔的值為列表
    if "," in value:
        items = [item.strip() for item in value.split(",")]
        # 嘗試將每個項目轉為適當的型別
        list_items = []
        for item in items:
            parsed_item = infer_type(item).value  # 遞歸解析列表項目
            list_items.append(ast.Constant(value=parsed_item))
        return ast.List(elts=list_items, ctx=ast.Load())

    # 字串（保留引號）
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return ast.Constant(value=value.strip('"').strip("'"))

    # 默認作為字串
    return ast.Constant(value=value)


def gen_ini(config: configparser.ConfigParser):
    cls_root = ast.ClassDef(
        "example_ini", body=[], decorator_list=[], bases=[], keywords=[]
    )
    # 使用class產生section
    for section in config.keys():
        if section == "DEFAULT":
            continue
        # 每一個section是一個inner_class
        section_cls_node = ast.ClassDef(
            section,
            body=[],
            decorator_list=[],
            bases=[],
            keywords=[],
        )

        # 每一個欄位是一個keyvalue pair
        for key in config[section]:
            class_var = ast.Assign(
                targets=[ast.Name(id=key, ctx=ast.Store())],
                value=infer_type(config[section][key]),
            )

            section_cls_node.body.append(class_var)

        # root 內有section
        cls_root.body.append(section_cls_node)

    strong_tree = ast.fix_missing_locations(cls_root)
    return ast.unparse(strong_tree)


def main():
    config = configparser.ConfigParser()
    file_path = "example.ini"
    config.read(file_path)
    py_str = gen_ini(config=config)
    with open(file_path.replace(".", "_") + ".py", "w", encoding="utf-8") as file:
        file.write(py_str)


main()

# 運行一次之後可以直接取得
# from example_ini import *

# print(example_ini.general.age)
