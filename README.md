# Talebook Skills

面向 AI 编程与自动化 Agent 的 [Talebook](https://github.com/talebook/talebook) Skill 集合。

## Skills

- `talebook`：通过 Talebook HTTP API 安全地搜索、浏览、上传、下载和管理书籍，操作有声书与远程书库，执行管理员任务，以及通过 Docker Compose 部署 Talebook。

## 安装

列出仓库中的 Skill：

```bash
npx skills add talebook/skills --list
```

安装 Talebook Skill：

```bash
npx skills add talebook/skills --skill talebook
```

也可以直接从本地仓库验证：

```bash
npx skills add . --list
```

## 使用

安装后，在支持 Agent Skills 的工具中提出 Talebook 相关任务，或显式调用 `$talebook`。

```text
使用 $talebook 检查我的 Talebook 实例当前登录身份和权限。
```

## 许可证

[BSD 2-Clause License](LICENSE)
