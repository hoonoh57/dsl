# UIA-1 Bridge/Runtime syntax fix

Status: REMOTE FIXED / USER-LOCAL REVALIDATION REQUIRED

Observed local failure:

```text
syntax-state-http
ChartAddonPersistenceHttpHost.mjs:46
```

Classification:

```text
Bridge / Runtime syntax defect
```

Cause:

```text
request.on('end', () => resolve(chunks.join(''));
```

had one missing closing parenthesis.

Fix:

```text
request.on('end', () => resolve(chunks.join('')));
```

No Core, Add-on semantic logic, or JSON state meaning changed.

Revalidation:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```
