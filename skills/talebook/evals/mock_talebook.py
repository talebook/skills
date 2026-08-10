#!/usr/bin/env python3
"""In-memory Talebook stand-in so the evals run without a real instance.

Only the endpoints the evals touch are implemented, with the response shapes the
CLI actually depends on (`user.is_login`, `user.is_admin`, `err`, `status.*`).
State is mutable, so a favorite or delete is visible to the follow-up read the
skill is supposed to make.

    python3 mock_talebook.py --port 8765
    TALEBOOK_URL=http://127.0.0.1:8765 python3 ../scripts/talebook-cli.py me status

Credentials: admin/hunter2 (admin), reader/reader-pass (normal), none (guest).
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse

ACCOUNTS = {
    "admin": {"password": "hunter2", "nickname": "管理员", "is_admin": True},
    "reader": {"password": "reader-pass", "nickname": "读者", "is_admin": False},
}

BOOKS = {
    1024: {"id": 1024, "title": "三体", "authors": ["刘慈欣"], "publisher": "重庆出版社",
           "tags": ["科幻"], "files": [{"format": "EPUB", "size": 512000}, {"format": "MOBI", "size": 604000}]},
    1025: {"id": 1025, "title": "三体Ⅱ 黑暗森林", "authors": ["刘慈欣"], "publisher": "重庆出版社",
           "tags": ["科幻"], "files": [{"format": "EPUB", "size": 733000}]},
    2048: {"id": 2048, "title": "测试书", "authors": ["临时"], "publisher": "",
           "tags": [], "files": [{"format": "TXT", "size": 2048}]},
}

FAVORITES: set[int] = set()
SEARCH_TASKS: dict[str, int] = {}

SETTINGS = {
    "site_title": "我的书库",
    "smtp_server": "smtp.example.com",
    "smtp_username": "books@example.com",
    "smtp_password": "smtp-secret-value",
    "douban_apikey": "douban-key-value",
    "invite_code": "0000",
    "allow_registry": True,
}


def identity(header: str | None) -> dict:
    if header and header.startswith("Basic "):
        try:
            raw = base64.b64decode(header[6:]).decode("utf-8")
            name, _, password = raw.partition(":")
        except (ValueError, UnicodeDecodeError):
            return {"is_login": False, "is_admin": False}
        account = ACCOUNTS.get(name)
        if account and account["password"] == password:
            return {"is_login": True, "is_admin": account["is_admin"],
                    "nickname": account["nickname"], "username": name}
    return {"is_login": False, "is_admin": False}


def user_info(user: dict) -> dict:
    return {
        "err": "ok",
        "sys": {"title": "我的书库", "books": len(BOOKS), "version": "3.10.0"},
        "user": user,
        "allow": {"register": True, "read": True, "download": True, "push": False},
        "upload": {"max_size": 200 * 1024 * 1024, "chunk_threshold": 20 * 1024 * 1024},
    }


def book_summary(book: dict) -> dict:
    return {"id": book["id"], "title": book["title"], "authors": book["authors"],
            "publisher": book["publisher"], "is_favorite": book["id"] in FAVORITES}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "MockTalebook/1"

    def do_GET(self) -> None:  # noqa: N802
        self.dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self.dispatch("POST")

    def dispatch(self, method: str) -> None:
        parts = parse.urlsplit(self.path)
        path = parts.path.rstrip("/") or "/"
        query = dict(parse.parse_qsl(parts.query))
        user = identity(self.headers.get("Authorization"))
        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except (ValueError, UnicodeDecodeError):
            body = {}
        try:
            payload = self.route(method, path, query, body, user)
        except KeyError:
            payload = {"err": "not_found", "msg": f"mock 未实现 {method} {path}"}
        self.send_json(payload)

    def route(self, method: str, path: str, query: dict, body: dict, user: dict) -> dict:
        if path == "/api/user/info":
            return user_info(user)

        if path == "/api/search":
            keyword = query.get("name", "")
            hits = [book_summary(b) for b in BOOKS.values() if keyword and keyword in b["title"]]
            return {"err": "ok", "total": len(hits), "books": hits}

        if path in ("/api/library", "/api/recent", "/api/hot"):
            items = [book_summary(b) for b in BOOKS.values()]
            return {"err": "ok", "total": len(items), "books": items}

        if path == "/api/favorites":
            if not user["is_login"]:
                return {"err": "user.need_login", "msg": "请先登录"}
            items = [book_summary(BOOKS[i]) for i in sorted(FAVORITES) if i in BOOKS]
            return {"err": "ok", "total": len(items), "books": items}

        match = re.fullmatch(r"/api/book/(\d+)", path)
        if match:
            book = BOOKS.get(int(match.group(1)))
            if book is None:
                return {"err": "book.not_found", "msg": "书籍不存在"}
            return {"err": "ok", "book": {**book_summary(book), "tags": book["tags"], "files": book["files"]}}

        match = re.fullmatch(r"/api/book/(\d+)/favorite", path)
        if match:
            if not user["is_login"]:
                return {"err": "user.need_login", "msg": "请先登录"}
            book_id = int(match.group(1))
            if book_id not in BOOKS:
                return {"err": "book.not_found", "msg": "书籍不存在"}
            FAVORITES.add(book_id) if body.get("favorite") else FAVORITES.discard(book_id)
            return {"err": "ok", "favorite": book_id in FAVORITES}

        match = re.fullmatch(r"/api/book/(\d+)/delete", path)
        if match:
            if not user["is_login"]:
                return {"err": "user.need_login", "msg": "请先登录"}
            book_id = int(match.group(1))
            if BOOKS.pop(book_id, None) is None:
                return {"err": "book.not_found", "msg": "书籍不存在"}
            FAVORITES.discard(book_id)
            return {"err": "ok", "deleted": book_id}

        if path == "/api/audios":
            return {"err": "ok", "total": 1, "audios": [
                {"book_id": 1024, "edition_id": 7, "title": "三体", "author": "刘慈欣",
                 "chapters": 3, "status": "published"}]}

        if path == "/api/network/sources":
            if not user["is_login"]:
                return {"err": "user.need_login", "msg": "请先登录"}
            return {"err": "ok", "sources": [
                {"id": 11, "name": "示例书源 A", "enabled": True},
                {"id": 12, "name": "示例书源 B", "enabled": True}]}

        if path == "/api/network/search":
            if not user["is_login"]:
                return {"err": "user.need_login", "msg": "请先登录"}
            task_id = f"task-{len(SEARCH_TASKS) + 1}"
            SEARCH_TASKS[task_id] = 0
            return {"err": "ok", "task_id": task_id, "status": "running", "keyword": query.get("key", "")}

        if path == "/api/network/search/status":
            task_id = query.get("task_id", "")
            if task_id not in SEARCH_TASKS:
                return {"err": "task.not_found", "msg": "搜索任务不存在"}
            SEARCH_TASKS[task_id] += 1
            polls = SEARCH_TASKS[task_id]
            # Stays running for a while on purpose: the skill must report progress
            # instead of busy-polling until it finishes.
            if polls < 4:
                return {"err": "ok", "task_id": task_id, "status": "running",
                        "finished": False, "books": []}
            return {"err": "ok", "task_id": task_id, "status": "finished", "finished": True,
                    "books": [{"source_id": 11, "name": "诡秘之主", "author": "爱潜水的乌贼",
                               "url": "https://example.invalid/book/1"}]}

        if path == "/api/admin/settings":
            if not user["is_admin"]:
                return {"err": "permission.not_admin", "msg": "需要管理员权限"}
            if method == "POST":
                SETTINGS.update(body)
                return {"err": "ok"}
            return {"err": "ok", "settings": dict(SETTINGS)}

        if path == "/api/admin/update":
            if not user["is_admin"]:
                return {"err": "permission.not_admin", "msg": "需要管理员权限"}
            return {"err": "ok", "status": {
                "has_update": True, "current_version": "3.10.0", "latest_version": "3.11.0",
                "latest_release_url": "https://github.com/talebook/talebook/releases/tag/v3.11.0"}}

        raise KeyError(path)

    def send_json(self, payload: dict) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock Talebook instance for skill evals")
    parser.add_argument("--port", type=int, default=8765, help="监听端口，0 表示随机，默认 8765")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"mock talebook on http://{args.host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
