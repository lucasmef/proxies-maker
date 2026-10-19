# Preview mínimo acelerado (experimental)

Variante do aplicativo principal com VideoToolbox para decodificar, reduzir resolução com `scale_vt` e codificar H.264 com `h264_videotoolbox`. Não há fallback para encoder de software.

O preset mantém maior lado de 320 px, 8 fps, alvo de vídeo de 60 kbps e cópia do áudio original. O destino mantém as subpastas de `Source` na pasta irmã `Preview`. Hardware ou formato incompatível causa erro.

Coloque FFmpeg compatível em `accelerated/bin/ffmpeg`. Nesta pasta, execute:

```sh
/usr/bin/python3 build_app.py
/usr/bin/python3 test_worker.py
```

O build gera `Preview mínimo acelerado.app`. Execute apenas quando desejar avaliar esta variante. Não há garantia de ganho de velocidade. Esta versão histórica usa logs e travas junto ao destino e não deve executar simultaneamente com a versão CPU para os mesmos arquivos.

Os scripts `benchmark.py`, `compare.py` e `test_hardware.py` recebem o caminho de um vídeo como primeiro argumento. `benchmark_comparison.py` recebe um ou mais caminhos e exige ambas as variantes instaladas em `~/Applications`. Mídias e resultados locais não são versionados.
