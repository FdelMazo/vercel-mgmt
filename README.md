# vercel-mgmt

Cancel multiple builds right from the terminal

```
VERCEL_TOKEN=<bearer_token> VERCEL_TEAM_ID=<team_id> uvx vercel-mgmt
or
uvx vercel-mgmt -t <bearer_token> -tid <team_id>
```

![](example.png)

Set `VI_MODE=True` for vim navigation (`j`/`k` to move, `g`/`G` for top/bottom).

```
VI_MODE=True uvx vercel-mgmt -t <bearer_token> -tid <team_id>
```

```
## DEBUGGING
# terminal 1
uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO -x WORKER
# terminal 2
uv run textual run --dev ./src/vercel_mgmt/mgmt.py -t <bearer_token> -tid <team_id>
```

```
## Updating
# update the version on pyproject.toml
uv lock
uv build
uv publish
```
