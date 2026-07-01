#!/usr/bin/env python3
"""母子手帳画像からワクチン接種記録表を生成する CLI。"""

from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mchhb.file_export import export_files
from mchhb.pipeline import process_images


def _collect_images(paths: tuple[str, ...], directory: str | None) -> list[Path]:
    images: list[Path] = []
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tiff"}

    for p in paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.iterdir()):
                if f.suffix.lower() in extensions:
                    images.append(f)
        elif path.suffix.lower() in extensions:
            images.append(path)
        else:
            raise click.ClickException(f"画像ファイルではありません: {path}")

    if directory:
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise click.ClickException(f"ディレクトリが見つかりません: {directory}")
        for f in sorted(dir_path.iterdir()):
            if f.suffix.lower() in extensions:
                images.append(f)

    seen: set[Path] = set()
    unique: list[Path] = []
    for img in images:
        resolved = img.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(img)
    return unique


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime if mime and mime.startswith("image/") else "image/jpeg"


@click.command()
@click.argument("images", nargs=-1, type=click.Path(exists=True))
@click.option("-d", "--directory", type=click.Path(exists=True), help="画像が入ったディレクトリ")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    default="output",
    help="出力ディレクトリ",
)
@click.option("--name", help="子どもの氏名（手帳から読み取れない場合）")
def main(images: tuple[str, ...], directory: str | None, output_dir: str, name: str | None) -> None:
    """母子手帳の画像からワクチン接種記録表（Excel / PDF）を作成します。"""
    load_dotenv()

    image_paths = _collect_images(images, directory)
    if not image_paths:
        raise click.ClickException("画像ファイルを指定してください（引数または --directory）")

    click.echo(f"{len(image_paths)} 枚の画像を処理します...")
    batch = []
    for p in image_paths:
        click.echo(f"  - {p}")
        batch.append((p.name, p.read_bytes(), _guess_mime(p)))

    result = process_images(batch)
    if name:
        result.child_name = name

    out = Path(output_dir)
    excel_path, pdf_path = export_files(result, out)
    click.echo(f"Excel: {excel_path}")
    click.echo(f"PDF:   {pdf_path}")
    click.echo(f"抽出件数: {len(result.vaccinations)} 件")

    if result.notes:
        click.echo("補足:")
        for note in result.notes:
            click.echo(f"  - {note}")


if __name__ == "__main__":
    main()
