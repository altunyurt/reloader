# Reloader - A simple auto-reloader for development

### Installation


```bash
git checkout https://github.com/altunyurt/reloader.git
cd reloader
uv tool install .
```

### Running

```bash
reloader -p WATCH_DIR -- COMMAND
```

COMMAND will be restarted when any file in WATCH_DIR is created / modified / deleted / moved .

```bash
reloader -p . -- uv run fastwsgi -p 9000 -l 1 wsgi:app
```

If for some reason environment variables are not passed correctly to the COMMAND, create a shell script and pass it to reloader

```bash

## serve.sh 
#!/bin/bash

export PYTHONPATH=.
# must be exec'd, otherwise reloader will only kill the shell script, not the child
exec uv run fastwsgi -p 9009 -l 1 wsgi:app

# command line
$ chmod +x serve.sh
$ reloader -p . -- ./serve.sh 
```
