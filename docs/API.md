# Referência de métodos

Todos os métodos que fazem I/O são `async` e devem ser aguardados com `await`. Os nomes abaixo
partem de uma instância chamada `panel`.

## Client

- `client.account`: `get`, `two_factor`, `enable_two_factor`, `disable_two_factor`,
  `update_email`, `update_password`, `activity`, `api_keys`, `create_api_key`, `delete_api_key`,
  `ssh_keys`, `add_ssh_key`, `remove_ssh_key`.
- `client.servers`: `list`, `iter`, `permissions`, `get`, `resources`, `activity`,
  `websocket_credentials`, `send_command`, `power`.
- `client.servers.databases`: `list`, `create`, `rotate_password`, `delete`.
- `client.servers.files`: `list`, `contents`, `write`, `download_url`, `upload_url`, `upload`,
  `rename`, `copy`, `compress`, `decompress`, `delete`, `create_folder`, `chmod`, `pull`.
- `client.servers.schedules`: `list`, `get`, `create`, `update`, `execute`, `delete`, `list_tasks`,
  `create_task`, `update_task`, `delete_task`.
- `client.servers.network`: `list`, `assign`, `update`, `set_primary`, `delete`.
- `client.servers.users`: `list`, `get`, `create`, `update`, `delete`.
- `client.servers.backups`: `list`, `get`, `create`, `download_url`, `toggle_lock`, `restore`,
  `delete`.
- `client.servers.startup`: `get`, `update_variable`.
- `client.servers.settings`: `rename`, `reinstall`, `update_docker_image`.

## Application

- `application.users`: `list`, `iter`, `get`, `get_by_external_id`, `create`, `update`, `delete`.
- `application.nodes`: `list`, `iter`, `get`, `deployable`, `configuration`, `create`, `update`,
  `delete`.
- `application.nodes.allocations`: `list`, `create`, `delete`.
- `application.locations`: `list`, `iter`, `get`, `create`, `update`, `delete`.
- `application.servers`: `list`, `iter`, `get`, `get_by_external_id`, `create`, `update_details`,
  `update_build`, `update_startup`, `suspend`, `unsuspend`, `reinstall`, `delete`.
- `application.servers.databases`: `list`, `get`, `create`, `update`, `reset_password`, `delete`.
- `application.nests`: `list`, `iter`, `get`.
- `application.nests.eggs`: `list`, `get`.

`schedules.list_tasks` e `application.servers.databases.update` constam na documentação PteroAPI,
mas não existem nas rotas do Panel 1.x sem modificações. Eles foram mantidos para instalações que
implementam essas extensões. `schedules.update_task` usa `POST`, conforme a rota oficial atual.

## WebSocket

- `websocket.credentials`, `websocket.connect`.
- Na conexão: `authenticate`, `refresh_token`, `send_event`, `send_command`, `set_power`,
  `request_logs`, `request_stats`, `receive`, `wait_for`, `events`, `close`.

## Acesso de baixo nível

- `panel.request(method, path, ...)` aceita caminhos sob `/api`.
- `panel.client.request(method, path, ...)` prefixa `/api/client`.
- `panel.application.request(method, path, ...)` prefixa `/api/application`.
- Passe `raw=True` em `panel.request` para receber o `httpx.Response` original.

