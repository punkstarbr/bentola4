# bentola4

Instalador leve para as ferramentas de linha de comando oficiais do [Bento4](https://www.bento4.com/), com foco em Google Colab e Linux x86_64.

O pacote Python não redistribui o SDK do Bento4. Ao executar `mp4decrypt` pela primeira vez, ele consulta a página oficial de downloads, identifica o pacote compatível com o sistema, baixa o SDK e executa o binário oficial a partir de `~/.local/share/bentola4`.

## Google Colab

Depois de publicar este repositório em `https://github.com/punkstarbr/bentola4`, use:

```python
!python -m pip install --upgrade --no-cache-dir "git+https://github.com/punkstarbr/bentola4.git"
```

A instalação do pacote não precisa de `sudo`. Na primeira execução, o wrapper baixa automaticamente o Bento4 oficial:

```python
!mp4decrypt 2>&1 | head -n 4
```

Depois, use o comando normalmente:

```python
!mp4decrypt --key 1:CHAVE entrada.mp4 saida.mp4
```

Para atualizar o SDK oficial para a versão mais recente:

```python
!bentola4 update
```

Para atualizar também o código do instalador a partir do GitHub:

```python
!python -m pip install --upgrade --no-cache-dir --force-reinstall "git+https://github.com/punkstarbr/bentola4.git"
!bentola4 update
```

O comando `pip install` não consegue executar automaticamente uma pós-instalação arbitrária de um projeto Python. Por isso, a instalação ocorre de forma preguiçosa na primeira chamada a `mp4decrypt`, ou explicitamente com `bentola4 install`.

## Diretório de instalação

Por padrão, os binários ficam em:

```text
~/.local/share/bentola4/
```

É possível escolher outro diretório:

```python
!BENTOLA4_HOME=/content/bento4 bentola4 install
```

Ou definir uma URL direta para um ZIP compatível:

```python
!BENTOLA4_URL="https://exemplo/bento4.zip" bentola4 install --force
```

## Uso em Python

```python
from bentola4.installer import executable

mp4decrypt = executable()
print(mp4decrypt)
```

## Plataformas

A descoberta automática contempla Linux x86_64, Linux ARM64 quando a página oficial disponibilizar esse arquivo, macOS e Windows x86_64. Em Google Colab padrão, o alvo esperado é Linux x86_64.

O pacote depende de acesso à internet no primeiro download e acompanha os termos de redistribuição do Bento4. O arquivo baixado deve ser conferido e utilizado conforme a licença oficial do Bento4.

## Desenvolvimento local

```bash
python -m pip install -e .
mp4decrypt 2>&1 | head -n 4
```

## Atualizações futuras

Para publicar uma alteração do instalador, faça commit e push neste repositório. O comando `pip install --upgrade` com a URL Git instala a versão atual do repositório. A versão do SDK do Bento4 é obtida da página oficial no momento da instalação/atualização, portanto não é necessário alterar o pacote a cada novo número de versão do SDK.
