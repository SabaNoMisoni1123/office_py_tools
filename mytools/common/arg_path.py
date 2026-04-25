# mytools\common\arg_path.py
"""
arg_paths.py

CLI引数など「文字列として渡されたパス」を、OS差分・環境差分を吸収しつつ
安全に Path に変換・解釈（相対→絶対）し、必要な検証まで行うためのユーティリティ。

設計方針（重要）:
- 「相対パスをどこ基準で解釈するか」を choose_base_dir() に集約し、
  それ以外の関数は base_dir を受け取るだけにして責務を分離する。
- 文字列の展開（~ や環境変数）と、Pathとしての解釈（相対/絶対、正規化）を分離する。
- 例外は ValueError / FileNotFoundError など「標準例外」を用い、CLI側で捕捉して整形しやすくする。

Python: 3.11+
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

# -----------------------------
# 内部ユーティリティ
# -----------------------------

_ENVVAR_PERCENT_PATTERN = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")

# kindの定義（validate_pathで利用）
PathKind = Literal["any", "file", "dir"]
DisplayStyle = Literal["native", "posix"]
PathFlavor = Literal["auto", "windows", "posix"]
BaseDirPrefer = Literal["cwd", "script"]


@dataclass(frozen=True)
class ResolvedPath:
    original: str
    expanded: str
    base_dir: Path
    path: Path


def _expand_percent_vars(s: str) -> str:
    """
    %VAR% 形式の環境変数を展開する。

    os.path.expandvars は Windows では %VAR% を扱えるが、
    POSIX上での挙動や実行環境（WSL等）をまたぐ場合に差が出得るため、
    ここで明示的に展開しておく。

    展開できない変数はそのまま残す（エラーにしない）。
    """

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return os.environ.get(key, m.group(0))

    return _ENVVAR_PERCENT_PATTERN.sub(repl, s)


def _make_absolute_without_resolving(p: Path) -> Path:
    """
    symlink解決やファイル存在確認はせずに「絶対パス化」する。

    - Path.resolve() は環境により symlink を辿ったり、存在しないパスでの挙動が変わるため、
      ここでは「絶対化」のみに使える Path.absolute() を採用する。
    """
    return p.absolute()


# -----------------------------
# 1) 入口：引数パスを「解釈して正規化」する
# -----------------------------


def resolve_cli_path(
    path_str: str,
    *,
    base_dir: Path | None = None,
    expand_user: bool = True,
    expand_vars: bool = True,
    resolve_symlinks: bool = False,
    flavor: PathFlavor = "auto",
) -> Path:
    """
    CLI引数など「文字列のパス」を、絶対 Path に変換する。

    典型的な期待動作:
    - 既に絶対パスなら、それを正規化して返す
    - 相対パスなら base_dir を基準に結合して絶対化する
      (base_dir が None の場合は choose_base_dir() を使う設計を推奨)

    文字列上の展開:
    - expand_user=True: "~" を展開
    - expand_vars=True: "$VAR", "${VAR}", "%VAR%" を展開

    resolve_symlinks:
    - True の場合のみ Path.resolve(strict=False) を呼び、可能な範囲で正規化する
      strict=False のため、存在しないパスでも例外になりにくいが、
      OSにより一部挙動差があり得る点に注意。

    flavor:
    - "auto": 実行OSに合わせる
    - "windows": "\" 区切りに寄せる
    - "posix": "/" 区切りに寄せる
    """
    if path_str is None:
        raise ValueError("path_str must not be None")
    s = str(path_str).strip()
    if not s:
        raise ValueError("path_str must not be empty")

    # 1) 文字列の展開（~ や環境変数）を先に行う
    s2 = expand_path_tokens(s, expand_user=expand_user, expand_vars=expand_vars)

    # 2) 区切り文字を必要に応じて寄せる（ただしPath生成前の軽い正規化）
    s3 = normalize_separators(s2, flavor=flavor)

    # 3) Path化
    p = Path(s3)

    # 4) 相対パスなら base_dir を基準に結合
    if base_dir is not None:
        base = Path(base_dir)
    else:
        # base_dir 未指定なら「実行時カレント」を使う（最小驚き）
        base = get_invocation_cwd()

    if not p.is_absolute():
        p = base / p

    # 5) 絶対化（symlinkは辿らない）
    p = _make_absolute_without_resolving(p)

    # 6) 必要に応じて symlink 解決や冗長要素解消を行う
    if resolve_symlinks:
        # strict=False: ファイルが存在しなくても解決を試みる。
        # ただし、実在しないパスの解釈にはOS差があり得るため、
        # 厳密な一貫性が必要なら resolve_symlinks=False を推奨。
        p = p.resolve(strict=False)

    return p


def resolve_many_cli_paths(
    paths: Iterable[str],
    *,
    base_dir: Path | None = None,
    expand_user: bool = True,
    expand_vars: bool = True,
    resolve_symlinks: bool = False,
    flavor: PathFlavor = "auto",
) -> list[Path]:
    """
    resolve_cli_path の複数版。
    """
    if paths is None:
        raise ValueError("paths must not be None")

    out: list[Path] = []
    for s in paths:
        out.append(
            resolve_cli_path(
                s,
                base_dir=base_dir,
                expand_user=expand_user,
                expand_vars=expand_vars,
                resolve_symlinks=resolve_symlinks,
                flavor=flavor,
            )
        )
    return out


# -----------------------------
# 2) 「基準ディレクトリ」を取得する
# -----------------------------


def get_invocation_cwd() -> Path:
    """
    「実行時点のカレントディレクトリ」を返す。

    - 典型的には、ユーザーがコマンドを実行した作業ディレクトリ。
    - CLI引数の相対パス解釈の基準として最も直感的。
    """
    return Path.cwd()


def get_script_dir(entry_file: str | Path) -> Path:
    """
    スクリプト（エントリポイント）ファイルの配置ディレクトリを返す。

    想定される渡し方:
    - 呼び出し元で: get_script_dir(__file__)
    - あるいは、エントリポイントとなる .py の Path を渡す

    注意:
    - entry_file が相対の場合もあり得るため、ここでは resolve(strict=False) を用いて
      なるべく絶対パスに寄せる。
    """
    if entry_file is None:
        raise ValueError("entry_file must not be None")
    p = Path(entry_file)
    # strict=False で、ファイルが存在しない状況でもある程度扱えるようにする
    p = p.resolve(strict=False)
    return p.parent


def choose_base_dir(
    *,
    base_dir: Path | None,
    prefer: BaseDirPrefer = "cwd",
    entry_file: str | Path | None = None,
) -> Path:
    """
    相対パス解釈の「基準ディレクトリ」を決定する。

    優先順位:
    1) base_dir が指定されていればそれを最優先
    2) base_dir が無ければ prefer に従う:
       - prefer="cwd": get_invocation_cwd()
       - prefer="script": get_script_dir(entry_file) ただし entry_file 未指定なら cwd にフォールバック

    フォールバックを例外ではなく「cwd」にする理由:
    - CLIツールでは、実行不能より「直感的に動く」ことが優先されるケースが多い。
    - 厳密にしたい場合は、呼び出し側で entry_file の未指定をエラー扱いにする。
    """
    if base_dir is not None:
        return Path(base_dir)

    if prefer == "cwd":
        return get_invocation_cwd()

    if prefer == "script":
        if entry_file is None:
            return get_invocation_cwd()
        return get_script_dir(entry_file)

    # 型的には到達しないが、防御的に
    return get_invocation_cwd()


# -----------------------------
# 3) 文字列展開（OS/環境差分を「文字列」段階で吸収）
# -----------------------------


def expand_path_tokens(
    path_str: str,
    *,
    expand_user: bool = True,
    expand_vars: bool = True,
) -> str:
    """
    文字列としてのパスに含まれるトークンを展開して返す。

    - "~" 展開（expand_user=True）
    - 環境変数展開（expand_vars=True）
      - $VAR, ${VAR}
      - %VAR%（独自展開→os.path.expandvars も併用）
    """
    if path_str is None:
        raise ValueError("path_str must not be None")

    s = str(path_str)

    if expand_vars:
        # %VAR% を先に展開（OS差を吸収）
        s = _expand_percent_vars(s)
        # $VAR / ${VAR} を展開（Windows上では %VAR% も扱えるが、ここでは冗長に許容）
        s = os.path.expandvars(s)

    if expand_user:
        # "~" 展開（Windows/POSIXともに対応）
        s = os.path.expanduser(s)

    return s


def normalize_separators(
    path_str: str,
    *,
    flavor: PathFlavor = "auto",
) -> str:
    """
    パス区切り文字（'/' と '\\'）の混在を、指定された flavor に寄せる。

    - flavor="auto": 実行OSに合わせる
    - flavor="windows": '\\' に寄せる
    - flavor="posix": '/' に寄せる

    注意:
    - UNCパス等の先頭 '\\\\' を壊しにくいよう、単純置換に留める。
    - ここは「見た目・入力の揺れを減らす」補助であり、
      実際の解釈は Path() に委ねる。
    """
    if path_str is None:
        raise ValueError("path_str must not be None")

    s = str(path_str)

    if flavor == "auto":
        flavor = "windows" if os.name == "nt" else "posix"

    if flavor == "windows":
        # POSIX区切りをWindows区切りに
        s = s.replace("/", "\\")
        return s

    if flavor == "posix":
        # Windows区切りをPOSIX区切りに
        s = s.replace("\\", "/")
        return s

    return s


# -----------------------------
# 4) 妥当性検証（CLI引数のエラーを早期に確定）
# -----------------------------


def validate_path(
    p: Path,
    *,
    must_exist: bool = False,
    kind: PathKind = "any",
    readable: bool | None = None,
    writable: bool | None = None,
) -> None:
    """
    Path の妥当性を検証し、問題があれば例外を送出する。

    must_exist:
      True なら p.exists() を要求する（存在しないなら FileNotFoundError）

    kind:
      - "any": 種別を問わない
      - "file": ファイルであることを要求（is_file）
      - "dir" : ディレクトリであることを要求（is_dir）

    readable / writable:
      - None: 検証しない
      - True: os.access で権限を要求する
      - False: 通常は使わない（敢えて禁止したい等の用途）。Falseの場合は「アクセス可能ならエラー」にする。

    例外型:
      - FileNotFoundError: must_exist=True かつ存在しない
      - NotADirectoryError / IsADirectoryError: kind不一致
      - PermissionError: 読み/書き権限条件に反する
      - ValueError: 引数不正など
    """
    if p is None:
        raise ValueError("p must not be None")

    path = Path(p)

    if must_exist and not path.exists():
        raise FileNotFoundError(str(path))

    if kind == "file":
        # must_exist=False でも、存在しているならファイルであることを要求する
        if path.exists() and not path.is_file():
            # ディレクトリだった場合など
            raise IsADirectoryError(str(path))

    elif kind == "dir":
        if path.exists() and not path.is_dir():
            raise NotADirectoryError(str(path))

    elif kind != "any":
        raise ValueError(f"Unsupported kind: {kind!r}")

    # readable/writable の判定は「存在しているときのみ」行うのが通常。
    # ただし must_exist=True の場合は存在が保証される。
    if path.exists():
        if readable is not None:
            can_read = os.access(path, os.R_OK)
            if readable and not can_read:
                raise PermissionError(f"Not readable: {path}")
            if (readable is False) and can_read:
                raise PermissionError(f"Readable but expected not readable: {path}")

        if writable is not None:
            can_write = os.access(path, os.W_OK)
            if writable and not can_write:
                raise PermissionError(f"Not writable: {path}")
            if (writable is False) and can_write:
                raise PermissionError(f"Writable but expected not writable: {path}")


def ensure_parent_dir(
    p: Path,
    *,
    create: bool = False,
) -> Path:
    """
    出力ファイル等の「親ディレクトリ」を返す。
    create=True の場合は親ディレクトリを作成する。

    例:
      out = resolve_cli_path("out/result.json", base_dir=...)
      ensure_parent_dir(out, create=True)
      out.write_text("...")

    注意:
    - p がディレクトリ自体を指す場合もあり得るが、
      ここでは「親」を返すだけに留める。
      目的が「出力先ディレクトリ」なら呼び出し側で p をディレクトリとして扱うこと。
    """
    if p is None:
        raise ValueError("p must not be None")

    path = Path(p)
    parent = path.parent

    if create:
        parent.mkdir(parents=True, exist_ok=True)

    return parent


# -----------------------------
# 5) 表示・ログ向け整形
# -----------------------------


def to_display_path(p: Path, *, style: DisplayStyle = "native") -> str:
    """
    ログ・エラーメッセージ用のパス表現を返す。

    style:
      - "native": OSネイティブ表現（str(Path)）
      - "posix" : 常に "/" 区切り（Path.as_posix）
    """
    if p is None:
        raise ValueError("p must not be None")

    path = Path(p)

    if style == "native":
        return str(path)

    if style == "posix":
        return path.as_posix()

    raise ValueError(f"Unsupported style: {style!r}")


# -----------------------------
# 追加: 追跡情報が欲しい場合のAPI（任意）
# -----------------------------


def resolve_cli_path_with_meta(
    path_str: str,
    *,
    base_dir: Path | None = None,
    prefer_base: BaseDirPrefer = "cwd",
    entry_file: str | Path | None = None,
    expand_user: bool = True,
    expand_vars: bool = True,
    resolve_symlinks: bool = False,
    flavor: PathFlavor = "auto",
) -> ResolvedPath:
    """
    resolve_cli_path のメタ情報付き版。

    「どの基準ディレクトリで解釈したか」「展開後文字列が何だったか」を
    呼び出し側がログ・デバッグ用途で参照できるようにする。
    """
    base = choose_base_dir(base_dir=base_dir, prefer=prefer_base, entry_file=entry_file)
    expanded = expand_path_tokens(
        path_str, expand_user=expand_user, expand_vars=expand_vars
    )
    normalized = normalize_separators(expanded, flavor=flavor)
    resolved = resolve_cli_path(
        normalized,
        base_dir=base,
        expand_user=False,  # 既に展開済み
        expand_vars=False,  # 既に展開済み
        resolve_symlinks=resolve_symlinks,
        flavor="auto",  # normalize済みなのでautoで十分（追加の置換は最小に）
    )
    return ResolvedPath(
        original=path_str, expanded=normalized, base_dir=base, path=resolved
    )
