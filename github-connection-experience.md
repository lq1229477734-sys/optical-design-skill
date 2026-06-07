# GitHub Connection and Upload Experience

This note records the practical workflow used to publish the `optical-design-skill` repository from a Windows Codex desktop environment.

Repository:

```text
https://github.com/lq1229477734-sys/optical-design-skill
```

Local publishing repository:

```text
D:\comsol\optical-design-skill-repo
```

## What Was Uploaded

The workflow successfully uploaded:

- `lighttools-design-skill/`
- `TMM skill/`
- `zemax-skill/`
- README updates
- README SVG visual assets under `assets/readme/`

The local file `github-connection-experience.md` was intentionally kept separate until the user asked to publish the upload experience.

## GitHub Connector Limitation

The GitHub connector could read repository files and reported repository permissions like:

```text
admin: true
push: true
pull: true
```

However, write calls still failed:

```text
403 Resource not accessible by integration
create-or-update-file-contents
```

The same failure happened for lower-level Git data API tree creation:

```text
403 Resource not accessible by integration
create-a-tree
```

Branch protection was checked read-only and was not the cause:

```text
main protected: false
```

Practical conclusion: the connector may show repository-level `push/admin` metadata while its integration token still lacks usable `Contents: Read and write` permission. When this happens, use the local Git publishing path instead of the connector write API.

## Working Local Git Runtime

The system `git` and `gh` commands were not available in PATH:

```text
where git
INFO: Could not find files for the given pattern(s).
```

GitHub Desktop provided a usable Git runtime. The previous working note used:

```text
C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.11
```

During the Zemax upload, GitHub Desktop had upgraded to:

```text
C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12
```

Useful current paths:

```text
C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe
C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\mingw64\bin\git.exe
C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\mingw64\bin\git-remote-https.exe
```

Use `cmd\git.exe` for local status/add/commit. Use `mingw64\bin\git.exe` for network push.

## Successful Commit Pattern

Check status:

```powershell
& "C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe" status --short --branch
```

Stage only intended files. Example for the Zemax skill:

```powershell
& "C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe" add README.md zemax-skill
```

Example for README visual assets:

```powershell
& "C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe" add README.md assets/readme
```

Commit with explicit local identity:

```powershell
& "C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe" -c user.name="Codex" -c user.email="codex@local" commit -m "Commit message"
```

## Successful Push Pattern

Set `GIT_EXEC_PATH` and prepend the `mingw64\bin` folder so Git can find the HTTPS remote helper:

```powershell
$env:GIT_EXEC_PATH="C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\mingw64\bin"
$env:PATH="C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\mingw64\bin;$env:PATH"
& "C:\Users\12294\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\mingw64\bin\git.exe" push
```

Without `GIT_EXEC_PATH`, HTTPS push can fail with:

```text
git: 'remote-https' is not a git command.
fatal: remote helper 'https' aborted session
```

## Successful Uploads In This Session

### Zemax Skill

Commit:

```text
d11e2bf Add Zemax skill
```

Push result:

```text
5cc878c..d11e2bf  main -> main
```

Files uploaded:

```text
zemax-skill/SKILL.md
zemax-skill/agents/openai.yaml
zemax-skill/references/nsc-workflow.md
zemax-skill/references/optimization-workflow.md
zemax-skill/references/zos-api-patterns.md
zemax-skill/scripts/zemax_connection_smoke.py
README.md
```

Excluded by request:

```text
magnifying_5lens
6-related files
```

### README Visuals

Commit:

```text
d6d22c5 Add README skill visuals
```

Push result:

```text
d11e2bf..d6d22c5  main -> main
```

Files uploaded:

```text
assets/readme/ecosystem-overview.svg
assets/readme/zemax-skill.svg
assets/readme/lighttools-design-skill.svg
assets/readme/tmm-skill.svg
README.md
```

## Verification

After each push, verify from GitHub, not only local Git status.

Use the GitHub connector to fetch:

```text
README.md
zemax-skill/SKILL.md
assets/readme/ecosystem-overview.svg
```

Successful verification showed:

- README contains image links under `assets/readme/`.
- `zemax-skill/SKILL.md` begins directly with `---`.
- SVG files are readable from the remote repository.

Local status after the README visual push showed only the intentionally untracked experience file:

```text
## main...origin/main
?? github-connection-experience.md
```

## Practical Lessons

- If connector writes return `403 Resource not accessible by integration`, check branch protection, but expect the root cause to be connector token scope.
- Repository metadata showing `push/admin` does not guarantee that the connector can use contents-write APIs.
- Keep a clean local publishing clone and push with GitHub Desktop's bundled Git when connector writes fail.
- GitHub Desktop version paths can change. Search under:

```text
C:\Users\12294\AppData\Local\GitHubDesktop
```

- Use `cmd\git.exe` for local operations and `mingw64\bin\git.exe` plus `GIT_EXEC_PATH` for HTTPS push.
- Stage only intended paths. Do not accidentally upload local notes or generated artifacts.
- For Codex skill files, keep frontmatter lowercase/hyphenated and verify no UTF-8 BOM before upload.

## Later Update: Approval Timeout And Small-Command Recovery

When updating `zemax-skill` again, both local publishing-repo writes and GitHub connector writes initially stalled with:

```text
The automatic permission approval review did not finish before its deadline.
```

This was not a GitHub repository error and not a user refusal. The command never reached the real filesystem or GitHub operation because the approval-review layer timed out.

What worked:

1. Ask the user for explicit approval again.
2. Split the operation into the smallest meaningful file writes instead of deleting/copying a whole directory.
3. Copy only the changed files first:

```powershell
Copy-Item -LiteralPath D:\ZEMAX\zemax-skill\references\patent-reproduction-workflow.md -Destination D:\comsol\optical-design-skill-repo\zemax-skill\references\patent-reproduction-workflow.md -Force
Copy-Item -LiteralPath D:\ZEMAX\zemax-skill\SKILL.md -Destination D:\comsol\optical-design-skill-repo\zemax-skill\SKILL.md -Force
```

Then the normal GitHub Desktop Git flow worked:

```text
848ee12 Update Zemax patent reproduction workflow
d6d22c5..848ee12  main -> main
```

Lesson: if approval times out, retry once with a smaller, more specific command. Treat timeout differently from rejection.

## Later Update: README Figure Generation With Python

For an academic README visual refresh, the `nature-figure` workflow required an explicit backend choice. The selected backend was Python.

The bundled Python initially lacked `matplotlib`:

```text
ModuleNotFoundError: No module named 'matplotlib'
```

After user-approved installation:

```powershell
C:\Users\12294\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install matplotlib
```

Two runtime details mattered:

- Set `MPLCONFIGDIR` to a writable workspace folder because matplotlib could not create `C:\Users\12294\.matplotlib`.
- Force the non-interactive backend with `mpl.use("Agg")` because the runtime did not have usable Tcl/Tk for the default Tk backend.

Working pattern:

```powershell
$env:MPLCONFIGDIR='D:\ZEMAX\.matplotlib'
C:\Users\12294\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\ZEMAX\make_academic_readme_figure.py
```

Generated artifact:

```text
D:\ZEMAX\ecosystem-overview-academic.svg
```

This figure is intended to replace the README's first visual asset:

```text
assets/readme/ecosystem-overview.svg
```
