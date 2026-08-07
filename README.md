# py-pterodactyl

Cliente Python totalmente assíncrono para a API do Pterodactyl Panel 1.x. O pacote cobre as APIs
Client, Application e WebSocket sem bloquear o event loop enquanto aguarda rede.

## Instalação

```bash
pip install py-pterodactyl
```

Para desenvolvimento local:

```bash
python -m pip install -e ".[dev]"
```

Requer Python 3.10 ou superior.

## Uso rápido

```python
import asyncio

from pterodactyl import Pterodactyl


async def main() -> None:
    async with Pterodactyl(
        "https://panel.exemplo.com",
        "ptlc_sua_chave_client",
    ) as panel:
        servidores = await panel.client.servers.list()
        await panel.client.servers.power("identificador", "start")
        recursos = await panel.client.servers.resources("identificador")
        print(servidores, recursos)


asyncio.run(main())
```

As respostas JSON são devolvidas sem alteração, inclusive os envelopes `object`, `attributes`,
`data` e `meta` usados pelo Panel. Respostas sem corpo retornam `None`; conteúdo de arquivo retorna
`str`; conteúdo binário retorna `bytes`.

## Client API

Cada grupo da documentação está disponível em um namespace previsível:

| Grupo | Acesso | Operações |
| --- | --- | --- |
| Conta | `panel.client.account` | perfil, 2FA, e-mail, senha, atividade, API keys e SSH keys |
| Servidores | `panel.client.servers` | listar, detalhes, recursos, atividade, comando, energia e credenciais WS |
| Bancos | `panel.client.servers.databases` | listar, criar, rotacionar senha e excluir |
| Arquivos | `panel.client.servers.files` | listar, ler, escrever, upload, download, copiar, renomear, compactar e permissões |
| Agendamentos | `panel.client.servers.schedules` | CRUD, executar e administrar tarefas |
| Rede | `panel.client.servers.network` | alocações, notas, primária e remoção |
| Subusuários | `panel.client.servers.users` | CRUD e permissões |
| Backups | `panel.client.servers.backups` | CRUD, download, bloqueio e restauração |
| Inicialização | `panel.client.servers.startup` | configuração e variáveis |
| Configurações | `panel.client.servers.settings` | renomear, reinstalar e imagem Docker |

Exemplo de arquivos e tarefas concorrentes:

```python
import asyncio

conteudo, bancos = await asyncio.gather(
    panel.client.servers.files.contents("abc123", "/server.properties"),
    panel.client.servers.databases.list("abc123"),
)

await panel.client.servers.schedules.create_task(
    "abc123",
    schedule=4,
    action="command",
    payload="say Reinício em 1 minuto",
    time_offset=0,
)
```

## Application API

Use uma chave `ptla_` criada na área administrativa:

```python
async with Pterodactyl(PANEL_URL, APPLICATION_KEY) as panel:
    usuario = await panel.application.users.create(
        email="ana@example.com",
        username="ana",
        first_name="Ana",
        last_name="Silva",
    )

    servidor = await panel.application.servers.create(
        name="Survival",
        user=usuario["attributes"]["id"],
        egg=1,
        docker_image="ghcr.io/pterodactyl/yolks:java_21",
        startup="java -jar server.jar",
        environment={"SERVER_JARFILE": "server.jar"},
        limits={"memory": 4096, "swap": 0, "disk": 10000, "io": 500, "cpu": 200},
        feature_limits={"databases": 2, "allocations": 1, "backups": 3},
        allocation={"default": 42},
    )
```

Os namespaces administrativos são `users`, `nodes`, `nodes.allocations`, `locations`, `servers`,
`servers.databases`, `nests` e `nests.eggs`. Métodos de criação e atualização de objetos complexos
aceitam os mesmos campos JSON documentados pelo Panel, o que mantém compatibilidade entre versões.

## Paginação, filtros e includes

```python
pagina = await panel.application.servers.list(
    include=["node", "user"],
    filters={"name": "Survival"},
    sort="-created_at",
    page=1,
    per_page=50,
)

async for servidor in panel.application.servers.iter(per_page=100):
    print(servidor["attributes"]["name"])
```

`iter()` busca as páginas sob demanda e respeita o fluxo assíncrono.

## WebSocket

O cliente obtém o JWT temporário no Panel, abre a conexão com Wings usando o subprotocolo
`pterodactyl` e envia a autenticação automaticamente:

```python
async with Pterodactyl(PANEL_URL, CLIENT_KEY) as panel:
    async with await panel.websocket.connect("abc123") as socket:
        await socket.request_logs()
        await socket.request_stats()
        await socket.send_command("list")

        async for message in socket:
            if message.event == "console output":
                print(message.data)
            elif message.event == "stats":
                print(message.data)
```

Também estão disponíveis `set_power("start|stop|restart|kill")`, `send_event()`, `receive()` e
`wait_for()`. Ao receber `token expiring`, a conexão renova o token automaticamente.

## Erros e endpoints personalizados

Erros HTTP são convertidos em `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
`ValidationError`, `RateLimitError` ou `PterodactylAPIError`. Todas preservam a resposta e a lista
`errors` do Panel.

```python
from pterodactyl import NotFoundError

try:
    await panel.client.servers.get("inexistente")
except NotFoundError as exc:
    print(exc.status_code, exc.errors)
```

Para extensões do Panel ou endpoints adicionados em versões futuras:

```python
resultado = await panel.request("GET", "/api/client/minha-extensao")
resultado = await panel.client.request("POST", "minha-extensao", json_data={"x": 1})
```

Consulte [API.md](docs/API.md) para o inventário de métodos.

## Referências

- [Client API](https://pteroapi.com/docs/api/client)
- [Application API](https://pteroapi.com/docs/api/application)
- [WebSocket API](https://pteroapi.com/docs/api/websocket)
- [Rotas oficiais do Pterodactyl Panel](https://github.com/pterodactyl/panel/tree/1.0-develop/routes)

## Licença

MIT.

