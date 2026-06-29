#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("BOHR_DATABASE_BASE_URL", "https://openapi.dp.tech")
META_FIELDS = {
    "_id",
    "audit_id",
    "authors",
    "build-in-source",
    "createTime",
    "create_time",
    "creator_ids",
    "is_locked",
    "owner_id",
    "projectName",
    "project_id",
    "status",
    "updateTime",
    "update_time",
}
INTERNAL_SUFFIXES = ("_audit_id", "_is_locked", "_owner_id", "_project_id", "_source", "_status")


def load_sdk():
    try:
        from bohrium_open_sdk.db import Op, SQLClient, Where
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: install with `python3 -m pip install \"bohrium-open-sdk>=1.0.5\"`"
        ) from exc
    return Op, SQLClient, Where


def client():
    access_key = os.environ.get("BOHR_ACCESS_KEY")
    if not access_key:
        raise SystemExit("BOHR_ACCESS_KEY is missing")
    _, SQLClient, _ = load_sdk()
    return SQLClient("", access_key, BASE_URL)


def json_arg(raw: str) -> Any:
    if raw.startswith("@"):
        return json.loads(Path(raw[1:]).read_text(encoding="utf-8"))
    return json.loads(raw)


def emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def call_with_retry(action):
    try:
        return action()
    except Exception as exc:  # noqa: BLE001
        message = str(exc).lower()
        if "timeout" not in message and "request canceled" not in message:
            raise
        time.sleep(2)
        return action()


def compact_row(row: Any) -> Any:
    if not isinstance(row, dict):
        return row
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if key in META_FIELDS or key.endswith(INTERNAL_SUFFIXES):
            continue
        if isinstance(value, dict) and "name" in value:
            compact[key] = {"name": value.get("name")}
        elif isinstance(value, list):
            compact[key] = [
                {"name": item.get("name")} if isinstance(item, dict) and "name" in item else item
                for item in value[:5]
            ]
        else:
            compact[key] = value
    return compact


def normalize_op(op_name: str):
    Op, _, _ = load_sdk()
    op_key = op_name.upper()
    if not hasattr(Op, op_key):
        valid = [name for name in dir(Op) if name.isupper()]
        raise SystemExit(f"Unsupported op {op_name!r}; valid: {', '.join(valid)}")
    return getattr(Op, op_key)


def normalize_value(op_name: str, value: Any) -> Any:
    if op_name.upper() == "BETWEEN" and isinstance(value, list):
        if len(value) != 2:
            raise SystemExit("BETWEEN list value must contain exactly two items")
        return f"{value[0]},{value[1]}"
    return value


def apply_conditions(table: Any, conditions: list[dict[str, Any]] | None) -> Any:
    if not conditions:
        return table
    _, _, Where = load_sdk()
    query = table
    for index, condition in enumerate(conditions):
        field = condition["field"]
        op_name = condition["op"]
        value = normalize_value(op_name, condition.get("value"))
        op = normalize_op(op_name)
        if index == 0:
            query = query.Where(field, op, value)
            continue
        where = Where(field, op, value)
        join = condition.get("join", "AND").upper()
        if join == "OR":
            query = query.Or(where)
        elif join == "AND":
            query = query.And(where)
        else:
            raise SystemExit("condition.join must be AND or OR")
    return query


def preview_rows(table_ak: str, conditions: list[dict[str, Any]] | None, limit: int = 20) -> dict[str, Any]:
    query = apply_conditions(client().table_with_ak(table_ak), conditions).page(1).page_size(limit)
    count, rows = call_with_retry(query.Find)
    return {"count": count, "rows": [compact_row(row) for row in rows[:limit]]}


def cmd_list_dbs(_: argparse.Namespace) -> None:
    data = client().base().Dbs()
    emit(
        [
            {"name": db.get("name"), "ak": db.get("ak"), "id": db.get("id"), "createTime": db.get("createTime")}
            for db in data.get("list", [])
        ]
    )


def cmd_list_tables(args: argparse.Namespace) -> None:
    result = client().db_with_ak(args.db_ak).Tables()
    tables = []
    for table in result.get("tables", []):
        fields = table.get("fields", [])
        tables.append(
            {
                "name": table.get("name"),
                "tableAk": table.get("tableAk"),
                "fieldCount": len(fields),
                "fieldsTruncated": len(fields) > args.max_fields,
                "fields": [
                    {"name": field.get("name"), "type": field.get("type")}
                    for field in fields[: args.max_fields]
                ],
            }
        )
    emit({"dbName": result.get("dbName"), "dbId": result.get("dbId"), "tables": tables})


def cmd_detail(args: argparse.Namespace) -> None:
    detail = client().table_with_ak(args.table_ak).Detail()
    emit(
        {
            "dbName": detail.get("dbName"),
            "tableName": detail.get("tableName"),
            "numberHeaderRows": detail.get("numberHeaderRows", 1),
            "fields": detail.get("fields", []),
            "schema": detail.get("schema", []),
        }
    )


def cmd_query(args: argparse.Namespace) -> None:
    conditions = json_arg(args.where) if args.where else None
    query = apply_conditions(client().table_with_ak(args.table_ak), conditions)
    if args.order_by:
        query = query.order(key=args.order_by, is_asc=not args.desc)
    query = query.page(args.page).page_size(args.page_size)
    count, rows = call_with_retry(query.Find)
    emit({"count": count, "page": args.page, "pageSize": args.page_size, "rows": [compact_row(row) for row in rows]})


def cmd_export(args: argparse.Namespace) -> None:
    try:
        from bohrium_open_sdk.db.func import db_query_full
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: install with `python3 -m pip install \"bohrium-open-sdk>=1.0.5\"`"
        ) from exc
    table = client().db_with_ak(args.db_ak)
    table.table_ak = args.table_ak
    count, df = call_with_retry(lambda: db_query_full(table, batch_size=args.batch_size))
    output = Path(args.output)
    if output.suffix.lower() == ".json":
        df.to_json(output, orient="records", force_ascii=False, indent=2)
    else:
        df.to_csv(output, index=False)
    emit({"count": count, "output": str(output)})


def cmd_insert(args: argparse.Namespace) -> None:
    rows = json_arg(args.rows)
    if not isinstance(rows, list):
        raise SystemExit("--rows must be a JSON array")
    result = client().table_with_ak(args.table_ak).Insert(rows)
    emit({"inserted": len(rows), "result": result})


def cmd_update(args: argparse.Namespace) -> None:
    conditions = json_arg(args.where) if args.where else None
    if not conditions and not args.allow_all:
        raise SystemExit("Refusing update without --where unless --allow-all is set")
    values = json_arg(args.set_values)
    if not args.yes:
        emit({"preview": preview_rows(args.table_ak, conditions), "next": "rerun with --yes to update"})
        return
    modify_count, success = call_with_retry(
        lambda: apply_conditions(client().table_with_ak(args.table_ak), conditions).Update(values)
    )
    emit({"updated": modify_count, "success": success})


def cmd_delete(args: argparse.Namespace) -> None:
    conditions = json_arg(args.where) if args.where else None
    if not conditions and not args.allow_all:
        raise SystemExit("Refusing delete without --where unless --allow-all is set")
    if not args.yes:
        emit({"preview": preview_rows(args.table_ak, conditions), "next": "rerun with --yes to delete"})
        return
    deleted_count = call_with_retry(
        lambda: apply_conditions(client().table_with_ak(args.table_ak), conditions).Delete()
    )
    emit({"deleted": deleted_count})


def cmd_create_table(args: argparse.Namespace) -> None:
    schema = json_arg(args.schema)
    table_ak = client().db_with_ak(args.db_ak).CreateTableV2(
        name=args.name,
        header_rows=args.header_rows,
        schema=schema,
    )
    emit({"tableAk": table_ak})


def cmd_alter_table(args: argparse.Namespace) -> None:
    schema = json_arg(args.schema)
    if not args.yes:
        emit({"schema": schema, "next": "rerun with --yes to alter table schema"})
        return
    result = client().table_with_ak(args.table_ak).AlterTable(schema)
    emit({"success": result})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bohrium custom database helper")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("list-dbs")
    p.set_defaults(func=cmd_list_dbs)

    p = sub.add_parser("list-tables")
    p.add_argument("db_ak")
    p.add_argument("--max-fields", type=int, default=30)
    p.set_defaults(func=cmd_list_tables)

    p = sub.add_parser("detail")
    p.add_argument("table_ak")
    p.set_defaults(func=cmd_detail)

    p = sub.add_parser("query")
    p.add_argument("table_ak")
    p.add_argument("--where")
    p.add_argument("--order-by")
    p.add_argument("--desc", action="store_true")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("export")
    p.add_argument("db_ak")
    p.add_argument("table_ak")
    p.add_argument("--output", required=True)
    p.add_argument("--batch-size", type=int, default=1000)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("insert")
    p.add_argument("table_ak")
    p.add_argument("--rows", required=True)
    p.set_defaults(func=cmd_insert)

    p = sub.add_parser("update")
    p.add_argument("table_ak")
    p.add_argument("--where")
    p.add_argument("--set", dest="set_values", required=True)
    p.add_argument("--allow-all", action="store_true")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete")
    p.add_argument("table_ak")
    p.add_argument("--where")
    p.add_argument("--allow-all", action="store_true")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("create-table")
    p.add_argument("db_ak")
    p.add_argument("name")
    p.add_argument("--schema", required=True)
    p.add_argument("--header-rows", type=int, default=1)
    p.set_defaults(func=cmd_create_table)

    p = sub.add_parser("alter-table")
    p.add_argument("table_ak")
    p.add_argument("--schema", required=True)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_alter_table)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
