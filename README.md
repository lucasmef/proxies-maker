# Preview mínimo · Proxies Maker

Gere previews leves de vídeos no macOS pelo menu **Abrir com** do Finder. O aplicativo preserva as subpastas da origem e copia o áudio sem recompressão, para facilitar a consulta de arquivos grandes.

## Como funciona

- Vídeo H.264 com maior lado de 320 px, proporção preservada, 8 fps e alvo de 60 kbps.
- Áudio original copiado. Áudio incompatível com MP4 gera erro.
- Fila com progresso por arquivo, cancelamento e inclusão de novos vídeos.
- Originais somente lidos; o preview anterior só é substituído após conversão bem-sucedida.

A pasta de entrada padrão é `~/Movies/Vídeos/Source` (o nome Vídeos usa acento decomposto no código). O destino é a pasta irmã `Preview`:

```text
Source/pasta/video.MOV → Preview/pasta/video_preview.mp4
```

Arquivos fora de `Source` são recusados. MOV, MP4 e M4V são aceitos. Arquivos com o mesmo nome-base e extensões diferentes compartilham o destino. Logs e travas da versão CPU ficam em `~/Library/Application Support/Preview mínimo`.

## Requisitos e build

macOS 13 ou superior, ferramentas de desenvolvimento da Apple com `swiftc` e `codesign`, Python 3 disponível em `/usr/bin/python3` e FFmpeg com `libx264`.

Coloque um executável compatível do FFmpeg em `bin/ffmpeg` e dê permissão de execução. Esse binário é uma dependência externa e não é distribuído neste repositório. A instalação local usou `imageio-ffmpeg 0.6.0` como origem do executável.

```sh
chmod +x bin/ffmpeg
/usr/bin/python3 build_app.py
```

O build gera `Preview mínimo.app` com scripts e FFmpeg incorporados. Copie o aplicativo para `~/Applications` e selecione vídeos no Finder: **Abrir com → Outro… → Preview mínimo**.

Para alterar a origem, ajuste `SOURCE` em `preview.py` e a pasta inicial do seletor em `Sources/PreviewMinimo.swift`, e refaça o build.

## Linha de comando

```sh
/usr/bin/python3 preview.py "$HOME/Movies/Vídeos/Source/pasta/video.MOV"
/usr/bin/python3 preview.py "$HOME/Movies/Vídeos/Source/pasta/video.MOV" --sample 10 --replace
```

`--sample` limita a duração; `--replace` refaz um preview existente; `--output` define um destino explícito para um único vídeo.

## Estrutura

| Arquivo | Função |
| --- | --- |
| `Sources/PreviewMinimo.swift` | Interface e fila do aplicativo |
| `preview.py` | Preset, caminhos e CLI |
| `worker.py` | Conversão cancelável e progresso JSON |
| `build_app.py` | Compilação e empacotamento |
| `test_worker.py` | Integração com mídia sintética |
| `build_workflow.py` | Gerador da ação rápida legada |
| `install_cpu_update.py` | Migração de instalação antiga |
| `accelerated/` | Variante experimental com VideoToolbox |

O script `install_cpu_update.py` migra logs e travas, substitui o app instalado e remove a variante acelerada instalada. Use-o somente em uma instalação antiga correspondente, com as conversões encerradas.

## Verificação

Com `bin/ffmpeg` disponível:

```sh
/usr/bin/python3 test_worker.py
```

O teste cria mídia sintética temporária e verifica conversão, progresso, subpastas, integridade dos pacotes AAC, decodificação e rejeição de origem externa.

## Variante acelerada e limites

A variante `accelerated/` usa VideoToolbox e não tem fallback de codificação por software. Requer FFmpeg compatível em `accelerated/bin/ffmpeg`. Consulte seu README antes de usar. O ganho depende do hardware, formato e carga de trabalho.

Não há tone mapping HDR específico. Os arquivos gerados são previews pequenos para consulta; avalie sua adequação antes de usá-los como proxies de edição.

## Privacidade

Mídia pessoal, amostras, logs, resultados de benchmark, ambientes virtuais, binários e aplicativos compilados ficam fora do Git por meio de `.gitignore`. Não adicione credenciais nem arquivos pessoais ao repositório.
