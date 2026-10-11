"""Build a portable anonymous ZIP from the audited public allowlist."""
import argparse
import hashlib
from pathlib import Path
import zipfile

from check_release import ROOT, check, public_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    check()
    destination = Path(args.output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = list(public_files())
    checksum_lines = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            name = file.relative_to(ROOT).as_posix()
            data = file.read_bytes()
            checksum_lines.append(hashlib.sha256(data).hexdigest() + "  " + name)
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
        entry = zipfile.ZipInfo("SHA256SUMS.txt", date_time=(2026, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, "\n".join(checksum_lines) + "\n")
    print(f"Packed {len(files)} public files plus checksums.")
    print(f"SHA-256: {hashlib.sha256(destination.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
