def main() -> None:
    DIST.mkdir(exist_ok=True)
    for lib in CP:
        if not lib.is_file():
            raise SystemExit(f"missing {lib}: copy it from the MREF appserver first")
    with tempfile.TemporaryDirectory() as out:
        sources = [str(p) for p in (HERE / "src").rglob("*.java")]
        subprocess.run(["javac", "--release", "21", "-nowarn", "-cp", os.pathsep.join(map(str, CP)), "-d", out, *sources], check=True)
        jar = DIST / "LocationReader.jar"
        with zipfile.ZipFile(jar, "w") as z:
            add(z, "META-INF/MANIFEST.MF", b"Manifest-Version: 1.0\r\n\r\n")
            for p in sorted(Path(out).rglob("*.class")):
                add(z, p.relative_to(out).as_posix(), p.read_bytes())
    web = DIST / "LocationReader_Web.zip"
    with zipfile.ZipFile(web, "w") as z:
        for p in sorted((HERE / "web").rglob("*")):
            if p.is_file():
                add(z, p.relative_to(HERE / "web").as_posix(), p.read_bytes())
    for f in (jar, web):
        print(f"{f.name}: {f.stat().st_size:,} bytes, {zipfile.ZipFile(f).namelist()}")
