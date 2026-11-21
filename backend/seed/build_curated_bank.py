"""Build finite, unsampled answer sets from the sources in source_manifest.json."""

import argparse
import base64
import csv
import hashlib
import html
import itertools
import json
import lzma
import re
import subprocess
import sys
import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, unquote, urljoin

SEED = Path(__file__).resolve().parent
sys.path.insert(0, str(SEED.parent))
from app.services.answer_validator import normalize_answer

BCD = "CC0-1.0 (MDN browser compatibility data)"
PYTHON = "PSF-2.0 documentation; API identifiers"
JAVA = "Oracle Java API documentation; API identifiers"
NODE = "MIT (Node.js documentation); API identifiers"
IANA = "IANA public registry; factual identifiers"
UNICODE = "Unicode-3.0"
DEBIAN = "Debian archive metadata; package identifiers"
GIT = "Git documentation; command and configuration identifiers"
POINTS = (10, 15, 30, 60, 85, 100)
DATE = "21 Nov 2026 UTC"
MDN = "https://developer.mozilla.org/docs/Web/"
JAVA_DOCS = "https://docs.oracle.com/en/java/javase/21/docs/api/"
PY_DOCS = "https://docs.python.org/3.12/"


# Use recognizable deep cuts where the catalog has a good fit. Each name is
# checked against the same candidate pool before assigning the sole Root Key.
EDITORIAL_KEYS = {
    "html-attributes": ("popover", "inputmode", "referrerpolicy"),
    "svg-attributes": ("pathLength", "baseFrequency"),
    "window-and-document": ("createTreeWalker", "getSelection", "fullscreenElement"),
    "element-and-node": ("getRootNode", "isEqualNode", "firstElementChild"),
    "canvas-and-webgl": ("getImageData", "isPointInPath", "stencilOpSeparate"),
    "javascript-text-values": ("codePointAt",),
    "py-os": ("os.posix_spawn",),
    "py-numbers": ("random.betavariate",),
    "py-sequences": ("str.removeprefix",),
    "py-files": ("tempfile.SpooledTemporaryFile", "pathlib.Path.samefile"),
    "py-async": ("asyncio.TaskGroup", "asyncio.as_completed"),
    "py-test": ("unittest.IsolatedAsyncioTestCase",),
    "py-network": ("socket.socket.sendfile", "http.client.HTTPConnection.set_tunnel"),
    "py-data-model": ("ast.literal_eval", "ast.ExceptHandler"),
    "py-binary": ("ctypes.BigEndianStructure", "struct.iter_unpack"),
    "py-inspection": ("importlib.invalidate_caches", "inspect.getclosurevars"),
    "py-gui": ("turtle.screensize", "turtle.setworldcoordinates"),
    "py-logging": ("logging.handlers.RotatingFileHandler",),
    "java-core-types": ("java.lang.StackWalker", "java.lang.reflect.AnnotatedArrayType"),
    "java-util-types": ("java.util.WeakHashMap", "java.util.IdentityHashMap"),
    "java-io-types": ("java.nio.channels.ScatteringByteChannel",),
    "java-network-types": ("java.net.http.WebSocket", "java.net.http.HttpClient.Redirect"),
    "java-swing-types": ("javax.swing.JLayer", "javax.swing.tree.TreePath"),
    "java-security-types": ("java.security.SecureRandomParameters", "java.security.cert.CertStoreParameters"),
    "java-data-types": ("javax.sql.rowset.CachedRowSet", "javax.sql.rowset.spi.SyncFactory"),
    "java-xml-types": ("javax.xml.stream.XMLEventReader", "javax.xml.crypto.dsig.keyinfo.PGPData"),
    "java-numeric-methods": ("BigInteger.modInverse", "BigInteger.compareTo"),
    "java-text-methods": ("Character.isBmpCodePoint",),
    "java-collection-methods": ("Arrays.mismatch", "Collections.unmodifiableNavigableMap"),
    "java-time-methods": ("LocalDate.datesUntil", "LocalDate.getChronology"),
    "node-files": ("opendir", "renameSync"),
    "node-streams": ("writeInt16LE",),
    "node-internet": ("domainToASCII",),
    "linguist-data": ("VCard", "Altium Designer"),
    "data-file-extensions": (".json5", ".jsproj"),
    "tldr-common": ("tac", "licensor"),
    "tldr-linux": ("getent", "run_init"),
    "tldr-osx": ("caffeinate", "dockutil"),
    "tldr-windows": ("wevtutil", "pptview"),
    "debian-database": ("pgbouncer", "postgresql-17-wal2json"),
    "debian-editors": ("vis", "elpa-bison-mode"),
    "debian-math": ("pari-gp", "octave-octclip"),
    "debian-vcs": ("fossil", "python3-hglib"),
    "debian-video": ("mkvtoolnix", "voctomix-outcasts"),
    "debian-graphics": ("povray", "tesseract-ocr-kaz"),
    "debian-sound": ("fluid-soundfont-gm", "drumstick-tools"),
    "git-config-keys": ("rerere.enabled", "receive.certNonceSlop"),
    "mime-images-video": ("image/avif", "video/vnd.hns.video"),
    "mime-audio": ("audio/opus", "audio/dsr-es202212"),
    "mime-text": ("text/troff", "text/rfc822-headers"),
    "mime-application": ("application/vnd.apple.mpegurl", "application/vnd.antix.game-component"),
    "iana-tcp-services": ("gopher", "sco-dtmgr"),
    "iana-udp-services": ("biff", "swift-rvf"),
    "ucd-basic-latin": ("REVERSE SOLIDUS", "LATIN SMALL LETTER Y"),
    "ucd-latin-1-supplement": ("SECTION SIGN", "LATIN CAPITAL LETTER O WITH TILDE"),
    "ucd-greek-and-coptic": ("GREEK SMALL LETTER FINAL SIGMA", "GREEK UPSILON WITH HOOK SYMBOL"),
    "ucd-mathematical-operators": ("N-ARY COPRODUCT", "DOES NOT SUCCEED OR EQUAL"),
    "ucd-miscellaneous-symbols": ("PERMANENT PAPER SIGN",),
    "ucd-arrows": ("LEFTWARDS DOUBLE ARROW WITH STROKE",),
    "emoji-smileys-emotion": ("upside-down face", "cat with tears of joy"),
    "emoji-animals-nature": ("sloth", "butterfly"),
    "emoji-food-drink": ("bubble tea", "pot of food"),
    "emoji-travel-places": ("flying saucer", "bridge at night"),
    "emoji-objects": ("abacus", "drop of blood"),
    "emoji-symbols": ("loop", "transgender symbol"),
}


@dataclass
class Answer:
    name: str
    url: str
    aliases: list = field(default_factory=list)


class Bank:
    def __init__(self, folder, sources):
        self.folder = folder
        self.sources = sources
        self.questions = []
        self.skipped = []

    def raw(self, key):
        return (self.folder / key).read_bytes()

    def text(self, key):
        return self.raw(key).decode("utf-8")

    def json(self, key):
        return json.loads(self.raw(key))

    def csv(self, key):
        return csv.DictReader(self.text(key).splitlines())

    def add(self, slug, category, prompt, scope, rows, license_name, popular="", key="", fuzzy=False, case_sensitive=False):
        # The gameplay uses casefolded inputs. Count case-only spellings as one
        # answer and suppress ambiguous shorthand aliases in favor of full names.
        def normalize(text):
            return normalize_answer(text, case_sensitive)

        by_name = {}
        for row in rows:
            name = normalize(row.name)
            if not name:
                raise ValueError(f"{slug}: invalid empty answer")
            if name in by_name:
                by_name[name].aliases.extend(row.aliases)
            else:
                by_name[name] = row
        n = len(by_name)
        if n < 100:
            self.skipped.append((slug, n))
            return
        anchors = {normalize(name): rank for rank, name in enumerate(popular.split("|")) if name}
        curated_keys = EDITORIAL_KEYS.get(slug, ())
        if curated_keys and not key:
            key = next((candidate for candidate in curated_keys if normalize(candidate) in by_name), "")
            if not key:
                raise ValueError(f"{slug}: no editorial Root Key is present in the source")
        featured = normalize(key)
        if featured and featured not in by_name:
            raise ValueError(f"{slug}: featured answer {key!r} not in source")
        ordered = sorted(by_name, key=lambda name: (
            min([anchors.get(name, 1000), *(anchors.get(normalize(a), 1000) for a in by_name[name].aliases)]),
            len(name), name,
        ))
        if not featured:
            # Pick a recognizable deep cut above the farthest end of the list.
            featured = ordered[(n * 74) // 100]
        ordered.remove(featured)
        alias_counts = Counter()
        for name, row in by_name.items():
            alias_counts.update({normalize(alias) for alias in row.aliases} - {name, ""})
        public = min(8, max(5, n // 18))
        trick = min(10, max(5, n // 14))
        cutoffs = (public, public + trick, (n - 1) * 44 // 100, (n - 1) * 77 // 100)
        answers = []
        for index, name in enumerate(ordered + [featured]):
            row = by_name[name]
            tier = 6 if name == featured else 1 + sum(index >= cutoff for cutoff in cutoffs)
            aliases = {}
            for alias in row.aliases:
                token = normalize(alias)
                if token and token not in by_name and alias_counts[token] == 1:
                    aliases.setdefault(token, alias)
            answers.append({
                "canonical": row.name, "aliases": sorted(aliases.values(), key=str.casefold),
                "rarity_tier": tier, "points": POINTS[tier - 1],
                "source_url": row.url, "license_name": license_name,
            })
        cat = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        self.questions.append({
            "slug": "curated-" + slug, "category": {"slug": cat, "name": category},
            "prompt": prompt, "scope": scope, "allow_fuzzy": fuzzy,
            "case_sensitive": case_sensitive, "status": "approved", "answers": answers,
        })

    def plain(self, slug, category, prompt, scope, names, url, license_name, **kwargs):
        self.add(slug, category, prompt, scope, (Answer(str(name), url) for name in names), license_name, **kwargs)


def documented(entries):
    return {name: item for name, item in entries.items() if name != "__compat" and "__compat" in item
            and not item["__compat"].get("status", {}).get("deprecated", False)}


def mdn_url(item, fallback):
    meta = item["__compat"]
    reference = meta.get("mdn_url") or meta.get("spec_url") or fallback
    return reference[0] if isinstance(reference, list) else reference


def web(bank):
    data = bank.json("bcd")
    version = data["__meta"]["version"]
    assert version == "8.1.10"
    catalog = f"MDN compatibility data {version}"
    scope = f"Direct entries in {catalog} that aren't marked deprecated."
    css = documented(data["css"]["properties"])
    bank.add("css-properties", "CSS", f"Name a CSS property in {catalog} that isn’t marked deprecated.",
             scope, (Answer(n, mdn_url(i, MDN + "CSS/Reference/Properties")) for n, i in css.items()),
             BCD, popular="color|display|margin|padding|width|height|font-size|background|opacity|transform|border|position",
             key="scroll-margin-inline", fuzzy=True)
    colors = re.findall(r'<th scope=row><dfn>([a-z]+)</dfn><td>#[0-9a-f]{6}', bank.text("css-colors"), re.I)
    assert len(colors) == 148
    bank.plain("css-color-names", "CSS", "Name a keyword from the CSS Color 4 named-colors table.",
               "All 148 named-color keywords. Functional colors and hex codes are separate syntaxes.",
               colors, "https://drafts.csswg.org/css-color-4/#named-colors", "W3C CSS Color 4; factual color identifiers",
               popular="red|blue|green|black|white|pink|yellow|orange|gray|tomato|lime|violet", key="papayawhip", fuzzy=True)
    selectors = documented(data["css"]["selectors"])
    selector_rows = []
    for name, item in selectors.items():
        url = mdn_url(item, MDN + "CSS/Reference/Selectors")
        tail = unquote(url.rsplit("/", 1)[-1])
        aliases = [tail] if tail.startswith(":") and tail.lstrip(":") == name else []
        selector_rows.append(Answer(name, url, aliases))
    bank.add("css-selectors", "CSS", f"Give a CSS selector entry name in {catalog} that isn’t marked deprecated.",
             scope + " Use its entry name, e.g. hover.", selector_rows, BCD,
             popular="hover|active|focus|checked|first-child|last-child|not|before|after|has|nth-child", key="placeholder-shown")
    for key, slug, label, anchors, featured in [
        ("elements", "html-elements", "HTML element", "div|p|a|span|img|input|button|h1|form|table|section|dialog", "wbr"),
    ]:
        entries = documented(data["html"][key])
        bank.add(slug, "HTML", f"Name an {label} in {catalog} that isn’t marked deprecated.",
                 scope, (Answer(n, mdn_url(i, MDN + "HTML/Reference/Elements"), [f"<{n}>"]) for n, i in entries.items()),
                 BCD, popular=anchors, key=featured)
    # The element-nested feature name is an explicit compatibility-data key.
    # MDN's attribute section or element page is retained for each key.
    for kind, category, anchors in [
        ("html", "HTML", "id|class|style|title|href|src|alt|type|name|value|disabled|target|placeholder|width|height|method"),
        ("svg", "SVG", "fill|stroke|viewBox|d|width|height|x|y|r|cx|cy|transform|points|stroke-width"),
    ]:
        rows = {}
        for node in [data[kind]["global_attributes"], *data[kind]["elements"].values()]:
            for name, item in documented(node).items():
                url = item["__compat"].get("mdn_url", "").replace("/en-US/docs/", "/docs/")
                spec = item["__compat"].get("spec_url", "")
                refs = [ref for ref in ([spec] if isinstance(spec, str) else spec) if ref]
                is_attribute = (name in data[kind]["global_attributes"] or "#attr-" in url
                                or "/Attribute/" in url or "#attributes" in url
                                or any("#attr-" in ref or re.search(r"#[A-Za-z0-9-]+Attribute$", ref) for ref in refs))
                if is_attribute:
                    source_file = item["__compat"].get("source_file") or kind + "/global_attributes.json"
                    catalog_ref = "https://github.com/mdn/browser-compat-data/blob/v8.1.10/" + source_file
                    rows.setdefault(name, Answer(name, url or (refs[0] if refs else catalog_ref)))
        bank.add(kind + "-attributes", category,
                 f"Name a global or element-specific {kind.upper()} attribute indexed as an attribute in {catalog}.",
                 "A non-deprecated BCD global attribute or element entry linked to an MDN or standards attribute reference. Shared names count once.",
                 rows.values(), BCD, popular=anchors)
    api = documented(data["api"])
    bank.add("web-api-interfaces", "Web APIs", f"Name a Web API interface in {catalog} that isn’t marked deprecated.",
             scope, (Answer(n, mdn_url(i, MDN + "API")) for n, i in api.items()), BCD,
             popular="Document|Window|Element|Node|Event|ArrayBuffer|Blob|File|URL|WebSocket|FormData|AbortController|MutationObserver",
             key="TreeWalker", fuzzy=True)
    for slug, group, types, common in [
        ("window-and-document", "Window or Document", ("Window", "Document"), "querySelector|alert|fetch|localStorage|title|body|cookie|createElement|setTimeout|getElementById|location"),
        ("element-and-node", "Node, Element, HTMLElement, or EventTarget", ("Node", "Element", "HTMLElement", "EventTarget"), "innerHTML|textContent|classList|id|appendChild|removeChild|addEventListener|click|closest|scrollIntoView"),
        ("canvas-and-webgl", "CanvasRenderingContext2D, WebGLRenderingContext, or WebGL2RenderingContext", ("CanvasRenderingContext2D", "WebGLRenderingContext", "WebGL2RenderingContext"), "fillRect|clearRect|fillText|lineTo|moveTo|arc|drawImage|stroke|fill|fillStyle|drawArrays|createBuffer"),
    ]:
        rows = []
        for parent in types:
            for name, item in documented(api[parent]).items():
                url = item["__compat"].get("mdn_url", "").replace("/en-US/docs/", "/docs/")
                if not url.startswith(MDN + "API/") or url.rsplit("/", 1)[-1] != name:
                    continue
                rows.append(Answer(name, url, [parent + "." + name]))
        bank.add(slug, "Graphics APIs" if "canvas" in slug else "Web APIs",
                 f"Name a non-deprecated {group} member documented in {catalog}.",
                 scope + " Only direct members with a matching MDN API page. Shared names count once.", rows, BCD, popular=common)
    groups = [
        ("javascript-collections", "Array, Object, Map, Set, or TypedArray", ("Array", "Object", "Map", "Set", "TypedArray"),
         "map|filter|reduce|forEach|find|keys|values|entries|has|set|get|push|pop|includes|from|assign"),
        ("javascript-text-values", "String, RegExp, Date, Math, or Number", ("String", "RegExp", "Date", "Math", "Number"),
         "slice|replace|length|split|trim|toLowerCase|abs|floor|max|min|random|parseInt|isNaN|getTime|test"),
    ]
    for slug, titles, types, anchors in groups:
        rows = []
        for owner in types:
            for n, i in documented(data["javascript"]["builtins"][owner]).items():
                url = i["__compat"].get("mdn_url", "").replace("/en-US/docs/", "/docs/")
                if url.startswith(MDN + "JavaScript/Reference/Global_Objects/") and url.rsplit("/", 1)[-1] == n:
                    rows.append(Answer(n, url, [owner + "." + n]))
        bank.add(slug, "JavaScript", f"Name a non-deprecated JavaScript member of {titles} in {catalog}.",
                 scope + " Direct members with matching MDN reference pages. Shared names count once.", rows, BCD, popular=anchors)
    for slug, categories, anchors in [
        ("browser-css-features", {"CSS", "CSS3", "CSS2"}, "CSS Grid|CSS Flexbox|CSS variables (Custom Properties)|CSS Transitions|CSS Animations|CSS position:sticky"),
        ("browser-js-features", {"JS API"}, "Fetch|WebSockets|Web Workers|Service Workers|IntersectionObserver|Geolocation|IndexedDB"),
    ]:
        rows = (Answer(v["title"], "https://caniuse.com/" + k, [k])
                for k, v in bank.json("caniuse")["data"].items() if categories.intersection(v["categories"]))
        bank.add(slug, "Browser compatibility",
                 f"Name a Can I Use feature tagged {', '.join(sorted(categories))} ({DATE} snapshot).",
                 "Every feature tagged with at least one named category in the pinned Can I Use catalog.", rows,
                 "CC-BY-4.0 (Can I Use dataset)", popular=anchors)


def python(bank):
    payload = bank.raw("python").split(b"\n", 4)
    assert payload[2] == b"# Version: 3.12"
    symbols = [line.split(None, 4)[:4] for line in zlib.decompress(payload[4]).decode().splitlines()]
    rows = (Answer(name, urljoin(PY_DOCS, location.replace("$", name)), [name.rsplit(".", 1)[-1]])
            for name, typ, _, location in symbols if typ == "py:module" and location.startswith("library/"))
    bank.add("python-stdlib-modules", "Python", "Name a module documented in the Python 3.12 standard-library inventory.",
             "All Python module entries whose documentation is in the versioned standard library.", rows, PYTHON,
             popular="os|sys|math|json|random|re|datetime|pathlib|collections|itertools|unittest|asyncio|sqlite3|typing",
             key="graphlib", fuzzy=True)
    groups = [
        ("py-os", "os", ("os",), {"py:function"}, "getcwd|listdir|mkdir|remove|rename|walk|chdir|stat|getenv|system|makedirs|getpid"),
        ("py-numbers", "math, cmath, statistics, or random", ("math","cmath","statistics","random"), {"py:function","py:method"}, "sqrt|sin|cos|tan|ceil|floor|log|mean|median|randint|choice|shuffle|uniform|sample|gcd"),
        ("py-functional", "itertools, functools, or operator", ("itertools","functools","operator"), {"py:function","py:class","py:method"}, "product|combinations|permutations|reduce|partial|lru_cache|chain|accumulate|itemgetter|attrgetter"),
        ("py-sequences", "str, bytes, bytearray, list, dict, tuple, or set", ("str","bytes","bytearray","list","dict","tuple","set"), {"py:method"}, "str.split|str.strip|str.replace|str.lower|list.append|list.sort|dict.get|list.extend|dict.items|set.add"),
        ("py-files", "pathlib, shutil, glob, os.path, tempfile, tarfile, or zipfile", ("pathlib","shutil","glob","os.path","tempfile","tarfile","zipfile"), {"py:function","py:method","py:class"}, "Path|exists|mkdir|glob|join|basename|dirname|copy|copytree|move|TemporaryDirectory|ZipFile"),
        ("py-async", "asyncio", ("asyncio",), {"py:function","py:method","py:class"}, "run|sleep|create_task|gather|Task|Future|Queue|Event|Lock|wait_for|TaskGroup"),
        ("py-test", "unittest or doctest", ("unittest","doctest"), {"py:function","py:method","py:class"}, "TestCase|assertEqual|assertTrue|assertRaises|setUp|tearDown|TestSuite|main|assertIn|testmod"),
        ("py-network", "socket, ssl, http, or urllib", ("socket","ssl","http","urllib"), {"py:function","py:method","py:class"}, "socket|connect|bind|listen|accept|send|recv|urlopen|urlparse|HTTPServer|SSLContext"),
        ("py-data-model", "typing or ast", ("typing","ast"), {"py:function","py:method","py:class"}, "Any|Optional|Union|Literal|TypedDict|Protocol|TypeVar|parse|walk|NodeVisitor|Constant"),
        ("py-binary", "struct, ctypes, or array", ("struct","ctypes","array"), {"py:function","py:method","py:class"}, "pack|unpack|calcsize|pack_into|Struct|array|append|frombytes|tobytes|sizeof|c_int|CDLL"),
        ("py-inspection", "sys, inspect, dis, or importlib", ("sys","inspect","dis","importlib"), {"py:function","py:method","py:class"}, "exit|getsizeof|signature|getsource|getmembers|import_module|reload|find_spec|isfunction|dis"),
        ("py-gui", "tkinter or turtle", ("tkinter","turtle"), {"py:function","py:method","py:class"}, "Tk|Button|Label|Canvas|Entry|Frame|mainloop|forward|left|right|penup|pendown|circle"),
        ("py-logging", "logging or warnings", ("logging","warnings"), {"py:function","py:method","py:class"}, "getLogger|basicConfig|debug|error|warning|info|warn|Logger|Handler|Formatter|filterwarnings"),
    ]
    kind_names = {"py:function": "function", "py:method": "method", "py:class": "class"}
    for slug, title, modules, kinds, anchors in groups:
        types = ", ".join(kind_names[k] for k in kind_names if k in kinds)
        rows = []
        for name, typ, _, location in symbols:
            if typ in kinds and any(name.startswith(module + ".") for module in modules):
                aliases = [name.rsplit(".", 1)[-1], name.removeprefix(modules[0] + ".")]
                rows.append(Answer(name, urljoin(PY_DOCS, location.replace("$", name)), aliases))
        bank.add(slug, "Python libraries", f"Name a documented Python 3.12 {types} under {title}.",
                 "All matching API inventory entries, including documented submodules. Qualify ambiguous names.",
                 rows, PYTHON, popular=anchors)
    rows = (Answer(name, urljoin(PY_DOCS, location.replace("$", name)), [name.rsplit(".", 1)[-1]])
            for name, typ, _, location in symbols if typ == "py:exception" and location.startswith("library/"))
    bank.add("py-exception", "Python", "Name an exception type documented in Python 3.12’s standard library.",
             "Every Python exception entry in the library inventory. Qualify ambiguous names.", rows, PYTHON,
             popular="ValueError|TypeError|IndexError|KeyError|RuntimeError|ImportError|FileNotFoundError|ZeroDivisionError|Exception",
             key="UnicodeTranslateError")


def oracle_index(bank, key):
    contents = bank.text(key)
    return json.loads(contents[contents.index("["):contents.rindex("]") + 1])


def java_path(item):
    package = item["p"]
    name = item.get("c", item["l"])
    modules = {
        "java.awt": "java.desktop", "javax.swing": "java.desktop", "java.rmi": "java.rmi",
        "java.net.http": "java.net.http", "java.sql": "java.sql", "javax.sql": "java.sql",
        "javax.xml.crypto": "java.xml.crypto", "javax.xml": "java.xml", "org.w3c.dom": "java.xml",
    }
    module = next((module for prefix, module in modules.items()
                   if package == prefix or package.startswith(prefix + ".")), "java.base")
    return JAVA_DOCS + module + "/" + package.replace(".", "/") + "/" + quote(name) + ".html"


def java(bank):
    groups = [
        ("java-core-types", "java.lang", ("java.lang",), "String|Object|Integer|Double|Math|Thread|RuntimeException|Class|System|Runnable|StringBuilder"),
        ("java-util-types", "java.util", ("java.util",), "ArrayList|HashMap|HashSet|List|Map|Set|Collections|Arrays|Iterator|Scanner|Optional|TreeMap|Random"),
        ("java-io-types", "java.io or java.nio", ("java.io","java.nio"), "File|InputStream|OutputStream|Reader|Writer|IOException|Path|Files|ByteBuffer|BufferedReader|FileReader"),
        ("java-network-types", "java.net, javax.net, or java.rmi", ("java.net","javax.net","java.rmi"), "URL|URI|Socket|ServerSocket|InetAddress|HttpClient|HttpRequest|HttpResponse|URLConnection|DatagramSocket"),
        ("java-awt-types", "java.awt", ("java.awt",), "Color|Point|Rectangle|Font|Graphics|Canvas|Button|Frame|EventQueue|MouseEvent|Window|Toolkit"),
        ("java-swing-types", "javax.swing", ("javax.swing",), "JFrame|JButton|JPanel|JLabel|JTextField|JTable|JList|JMenu|JDialog|JOptionPane"),
        ("java-security-types", "java.security or javax.crypto", ("java.security","javax.crypto"), "MessageDigest|SecureRandom|Signature|Cipher|KeyPair|KeyPairGenerator|Mac|SecretKey|KeyStore|Provider"),
        ("java-data-types", "java.sql or javax.sql", ("java.sql","javax.sql"), "Connection|DriverManager|Statement|PreparedStatement|ResultSet|SQLException|DataSource|Types|Date|Timestamp"),
        ("java-xml-types", "javax.xml or org.w3c.dom", ("javax.xml","org.w3c.dom"), "Document|Element|Node|NodeList|DocumentBuilder|DocumentBuilderFactory|XMLStreamReader|XPath|Transformer"),
    ]
    types = oracle_index(bank, "java-types")
    for slug, title, packages, anchors in groups:
        rows = [Answer(item["p"] + "." + item["l"], java_path(item), [item["l"], item["l"].rsplit(".", 1)[-1]])
                for item in types if any(item.get("p", "") == p or item.get("p", "").startswith(p + ".") for p in packages)]
        bank.add(slug, "Java libraries", f"Name a type in Java 21’s {title} package families.",
                 "All matching Java SE/JDK 21 type-index entries, including subpackages and nested types. Qualify ambiguous names.",
                 rows, JAVA, popular=anchors)
    members = oracle_index(bank, "java-members")
    for slug, title, owners, anchors in [
        ("java-numeric-methods", "Math, StrictMath, BigDecimal, or BigInteger", {"Math","StrictMath","BigDecimal","BigInteger"}, "Math.abs|Math.max|Math.min|Math.pow|Math.sqrt|Math.round|Math.floor|BigInteger.gcd|BigDecimal.add"),
        ("java-text-methods", "String, StringBuilder, StringBuffer, Character, Pattern, or Matcher", {"String","StringBuilder","StringBuffer","Character","Pattern","Matcher"}, "String.substring|String.length|String.charAt|String.split|String.equals|StringBuilder.append|Character.isDigit|Pattern.compile|Matcher.find"),
        ("java-collection-methods", "Arrays, Collections, List, or Map", {"Arrays","Collections","List","Map"}, "Arrays.sort|Arrays.asList|Arrays.binarySearch|Collections.sort|Collections.reverse|List.add|List.of|Map.get|Map.put"),
        ("java-time-methods", "LocalDate, LocalDateTime, ZonedDateTime, Instant, Duration, or Period", {"LocalDate","LocalDateTime","ZonedDateTime","Instant","Duration","Period"}, "LocalDate.now|LocalDate.of|LocalDate.parse|Instant.now|LocalDate.plusDays|Duration.between|Period.ofDays"),
    ]:
        rows = []
        for item in members:
            owner, signature = item.get("c"), item["l"]
            if owner not in owners or "(" not in signature or signature.startswith(owner + "("):
                continue
            package = item.get("p", "")
            if slug == "java-collection-methods" and package != "java.util":
                continue
            if not package.startswith("java."):
                continue
            name = signature.split("(", 1)[0]
            rows.append(Answer(owner + "." + name, java_path(item),
                               [name, name + "()", owner + "." + name + "()", item["p"] + "." + owner + "." + name]))
        bank.add(slug, "Java APIs", f"Name a Java 21 method on {title}.",
                 "Use a method name without a signature. Overloads count once. Qualify ambiguous names with the declaring class.",
                 rows, JAVA, popular=anchors)


def nodejs(bank):
    docs = {entry["name"]: entry for entry in bank.json("node")["modules"]}

    def methods(node, url):
        for method in node.get("methods", []):
            name = method["name"]
            name_from_signature = method.get("textRaw", "").lstrip("`").split("(", 1)[0]
            yield Answer(name, url, [name + "()", name_from_signature])
        for collection in ("classes", "modules", "miscs", "globals"):
            for child in node.get(collection, []):
                yield from methods(child, url)

    groups = [
        ("node-files", "fs or path", ("fs", "path"), "readFile|writeFile|appendFile|open|close|mkdir|readdir|stat|unlink|join|dirname|basename|resolve|normalize|isAbsolute"),
        ("node-servers", "http, https, or net", ("http", "https", "net"), "createServer|request|get|listen|end|write|setHeader|getHeader|close|connect|destroy"),
        ("node-streams", "stream, buffer, or zlib", ("stream", "buffer", "zlib"), "pipeline|pipe|write|read|from|alloc|toString|slice|createGzip|gzip|gunzip|inflate|deflate"),
        ("node-crypto", "crypto or Web Crypto API", ("crypto", "web_crypto_api"), "createHash|createHmac|digest|update|randomBytes|randomUUID|generateKeyPair|verify|sign|encrypt|decrypt"),
        ("node-testing", "assert, test, or perf_hooks", ("assert", "test_runner", "performance_measurement_apis"), "equal|deepEqual|strictEqual|throws|rejects|ok|test|skip|describe|run|mark|measure|now"),
        ("node-processes", "child_process, worker_threads, events, or cluster", ("child_process", "worker_threads", "Events", "cluster"), "spawn|exec|execFile|fork|emit|on|once|off|postMessage|terminate|disconnect|kill"),
        ("node-internet", "DNS, URL, TLS, or datagram sockets", ("dns", "url", "tls_(ssl)", "dgram"), "lookup|resolve|resolve4|reverse|parse|format|connect|createServer|createSocket|send|bind"),
        ("node-cli", "os, util, or readline", ("os", "util", "readline"), "platform|hostname|arch|cpus|freemem|inspect|format|promisify|callbackify|createInterface|question"),
        ("node-web-streams", "Web Streams API, stream, or timers", ("web_streams_api", "stream", "timers"), "getReader|getWriter|close|write|read|enqueue|cancel|setTimeout|clearTimeout|pipe|pipeline"),
    ]
    for slug, title, modules, anchors in groups:
        rows = []
        for module in modules:
            section = Path(docs[module]["source"]).stem
            ref = "https://nodejs.org/dist/v22.16.0/docs/api/" + section + ".html"
            rows.extend(methods(docs[module], ref))
        bank.add(slug, "Node.js", f"Name a method documented for {title} in Node.js 22.16.",
                 "Methods in the specified Node.js documentation chapters. Shared method names count once.",
                 rows, NODE, popular=anchors)


def tools(bank):
    import yaml

    linguist = yaml.safe_load(bank.text("linguist"))
    linguist_ref = bank.sources["linguist"].replace("raw.githubusercontent.com", "github.com").replace(
        "/cfd7a0113aa1efab99faeff38756f0ed4d48add8/", "/blob/cfd7a0113aa1efab99faeff38756f0ed4d48add8/")
    for kind, title, anchors, featured in [
        ("programming", "programming language", "Python|Java|JavaScript|TypeScript|C|C++|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Lua|R|Bash", "Forth"),
        ("data", "data language or format", "JSON|YAML|CSV|TOML|XML|INI|SVG|JSON5|TSV|Dockerfile|dotenv", ""),
        ("markup", "markup language or format", "HTML|Markdown|LaTeX|Handlebars|AsciiDoc|Jinja|reStructuredText|Roff", ""),
    ]:
        rows = (Answer(name, linguist_ref, meta.get("aliases", [])) for name, meta in linguist.items() if meta["type"] == kind)
        bank.add("linguist-" + kind, "Languages and formats",
                 f"Name a {title} classified as {kind} by GitHub Linguist ({DATE} snapshot).",
                 "All entries of the specified Linguist type in the pinned version.", rows, "MIT (GitHub Linguist metadata)",
                 popular=anchors, key=featured, fuzzy=True)
    exts = (Answer(ext, linguist_ref, [ext.lstrip(".")]) for meta in linguist.values()
            if meta["type"] == "programming" for ext in meta.get("extensions", ()))
    bank.add("source-file-extensions", "Languages and formats",
             f"Name a source-file extension listed for a GitHub Linguist programming language ({DATE} snapshot).",
             "All extensions declared for at least one programming entry in the pinned Linguist catalog.", exts,
             "MIT (GitHub Linguist metadata)", popular=".py|.java|.js|.ts|.c|.cpp|.cs|.go|.rs|.rb|.php|.sh|.swift|.kt|.lua", key=".f90")
    data_exts = (Answer(ext, linguist_ref, [ext.lstrip(".")]) for meta in linguist.values()
                 if meta["type"] in {"data", "markup"} for ext in meta.get("extensions", ()))
    bank.add("data-file-extensions", "Languages and formats",
             f"Name an extension listed for a GitHub Linguist data or markup format ({DATE} snapshot).",
             "All extensions declared by Linguist entries classified data or markup.", data_exts,
             "MIT (GitHub Linguist metadata)", popular=".json|.xml|.yaml|.yml|.html|.md|.csv|.toml|.ini|.svg|.rst")

    tldr = bank.json("tldr")
    assert tldr["sha"] == "41ea8214c82f3d16ab758bd8a41d85a559baae3e" and not tldr["truncated"]
    for platform, title, anchors in [
        ("common", "cross-platform / common", "git|python|python3|node|npm|curl|grep|sed|awk|cat|ls|cp|ls|find|zip|unzip|make"),
        ("linux", "Linux", "apt|apt-get|systemctl|lsblk|ip|fdisk|dmesg|mount|umount|pacman|dnf|free|top|journalctl"),
        ("osx", "macOS", "brew|pbcopy|pbpaste|open|softwareupdate|launchctl|diskutil|defaults|sw_vers|sips"),
        ("windows", "Windows", "ipconfig|dir|copy|robocopy|winget|powershell|cmd|tasklist|taskkill|where|chkdsk"),
    ]:
        prefix = "pages/" + platform + "/"
        rows = []
        for item in tldr["tree"]:
            path = item["path"]
            rest = path.removeprefix(prefix)
            if path.startswith(prefix) and re.fullmatch(r"[a-zA-Z0-9_.+]+\.md", rest):
                rows.append(Answer(rest[:-3], "https://github.com/tldr-pages/tldr/blob/" + tldr["sha"] + "/" + quote(path)))
        bank.add("tldr-" + platform, "Command line", f"Name a single, unhyphenated command listed under {title} in English tldr ({DATE} snapshot).",
                 "A single command name consisting of letters, digits, dots, underscores, or pluses in that platform folder. Subcommand pages are separate.",
                 rows, "MIT (tldr-pages); command identifiers", popular=anchors)
    repos = lzma.decompress(bank.raw("debian")).decode().split("\n\n")
    release = bank.text("debian-release")
    assert "Version: 13.8\n" in release
    per_section = {}
    for row in repos:
        fields = dict(re.findall(r"^(Package|Section|Architecture): (.+)$", row, re.M))
        if fields.get("Architecture") in {"all", "amd64"}:
            per_section.setdefault(fields["Section"], []).append(Answer(
                fields["Package"], "https://packages.debian.org/trixie/" + fields["Package"]))
    sections = [
        ("database", "databases", "postgresql|sqlite3|mariadb-server|redis-server|mysql-common|pgadmin4|dbeaver|postgresql-client"),
        ("editors", "editors", "vim|nano|emacs|neovim|gedit|kate|mousepad|geany|jed|joe|mg"),
        ("interpreters", "interpreters", "python3|ruby|nodejs|tcl|lua5.4|gawk|mawk|guile-3.0|php-cli"),
        ("math", "mathematics", "octave|r-base|bc|dc|gnuplot|maxima|sagemath|pari-gp|gap"),
        ("web", "web software", "chromium|firefox-esr|wget|lynx|w3m|lighttpd|nginx|apache2|curl"),
        ("httpd", "HTTP servers and related tools", "apache2|nginx|lighttpd|caddy|gunicorn|boa|fcgiwrap"),
        ("vcs", "version control", "git|subversion|mercurial|cvs|bzr|fossil|darcs|tig|git-lfs|gitk"),
        ("video", "video software", "ffmpeg|vlc|mpv|mplayer|handbrake|obs-studio|kdenlive|avidemux|x264"),
        ("graphics", "graphics", "gimp|inkscape|blender|imagemagick|krita|graphviz|darktable|gifsicle|optipng"),
        ("sound", "audio software", "audacity|sox|alsa-utils|pulseaudio|pipewire|flac|lame|espeak|ffmpeg"),
        ("comm", "communications", "minicom|picocom|screen|mosquitto|putty|cu|kermit|cutecom"),
        ("electronics", "electronics", "kicad|ngspice|arduino|fritzing|iverilog|verilator|yosys|gtkwave"),
        ("text", "text processing", "pandoc|less|jq|tidy|groff|hunspell|aspell|gettext|dos2unix|xmlstarlet"),
        ("mail", "email software", "thunderbird|mutt|neomutt|postfix|exim4|mailutils|fetchmail|procmail|spamassassin"),
    ]
    for section, topic, anchors in sections:
        bank.add("debian-" + section, "Debian " + ("tools" if section in {"editors","interpreters","vcs","text"} else "packages"),
                 f"Name a Debian 13.8 package in the {section} section for {topic}.",
                 "Every amd64 or architecture-independent package in the pinned Debian trixie main package index section.",
                 per_section[section], DEBIAN, popular=anchors)
    commands = (Answer(name, "https://git-scm.com/docs/" + name, ["git " + name[4:]])
                for line in bank.text("git").splitlines() if re.match(r"^git-[a-z0-9-]+\s", line)
                for name in [line.split()[0]])
    bank.add("git-commands", "Version control", "Name a command in Git 2.50.1’s command classification list.",
             "Every git-* entry in command-list.txt, including plumbing commands. Use git name or git-name.",
             commands, GIT, popular="git-add|git-commit|git-status|git-clone|git-init|git-push|git-pull|git-fetch|git-log|git-diff|git-merge|git-rebase", key="git-range-diff")
    config_ref = "https://git-scm.com/docs/git-config/2.50.0"
    config = []
    for identifier, label in re.findall(r'<dt[^>]*?id="(Documentation/git-config\.txt-[^"]+)"[^>]*>(.*?)</dt>', bank.text("git-config"), re.S):
        name = html.unescape(re.sub(r"<[^>]*>", "", label)).strip()
        if re.fullmatch(r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+", name):
            config.append(Answer(name, config_ref + "#" + quote(identifier)))
    bank.add("git-config-keys", "Version control", "Name a fixed dotted configuration key in Git 2.50’s git-config manual.",
             "Complete list of dotted, literal key headings. Keys that require replacing a placeholder are excluded.",
             config, GIT, popular="user.name|user.email|core.editor|core.autocrlf|core.ignorecase|init.defaultBranch|pull.rebase|push.default|color.ui|credential.helper")
    spdx = bank.json("license")
    rows = (Answer(item["licenseId"], item["reference"], [item["name"]]) for item in spdx["licenses"]
            if not item["isDeprecatedLicenseId"])
    bank.add("spdx-license", "Software licenses", f"Name an SPDX license identifier that isn’t deprecated ({DATE} snapshot).",
             "All current identifiers in the pinned SPDX License List. Unique full license names are also accepted.",
             rows, "CC0-1.0 (SPDX list metadata)", popular="MIT|Apache-2.0|GPL-3.0-only|BSD-3-Clause|GPL-2.0-only|MPL-2.0|ISC|AGPL-3.0-only|Unlicense|CC0-1.0",
             key="BlueOak-1.0.0")
    keys = re.findall(r"<li>([A-Z_]+)</li>", bank.text("sqlite"))
    assert len(keys) == 147
    bank.plain("sqlite-keywords", "SQL", f"Name a SQL keyword in SQLite’s master keyword list ({DATE} snapshot).",
               "The entire SQLite keyword table, including keywords build options can disable.",
               keys, "https://www.sqlite.org/lang_keywords.html", "SQLite documentation; SQL keyword identifiers",
               popular="SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|TABLE|JOIN|ORDER|GROUP|LIMIT|HAVING", key="PRECEDING")


def registries(bank):
    for slug, types, anchors in [
        ("mime-images-video", ("image","video"), "image/png|image/jpeg|image/gif|image/webp|image/svg+xml|video/mp4|video/webm|video/quicktime"),
        ("mime-audio", ("audio",), "audio/mpeg|audio/ogg|audio/wav|audio/flac|audio/aac|audio/mp4|audio/webm|audio/opus"),
        ("mime-text", ("text",), "text/plain|text/html|text/css|text/javascript|text/csv|text/markdown|text/xml|text/calendar"),
        ("mime-application", ("application",), "application/json|application/pdf|application/xml|application/zip|application/octet-stream|application/wasm|application/gzip|application/graphql"),
    ]:
        entries = []
        for media in types:
            for item in bank.csv(media):
                label = media + "/" + item["Name"].split(" (", 1)[0]
                url = "https://www.iana.org/assignments/media-types/media-types.xhtml#" + media
                entries.append(Answer(label, url, [item["Template"]]))
        bank.add(slug, "Internet formats", f"Name an IANA-registered {' or '.join(types)} media type ({DATE} snapshot).",
                 "Use type/subtype. All names in the named IANA media type registries, including vendor types.",
                 entries, IANA, popular=anchors)
    records = [Answer(item["Name"], "https://www.iana.org/assignments/character-sets",
                      [item["Preferred MIME Name"], *item["Aliases"].split()])
               for item in bank.csv("charsets")]
    bank.add("iana-character-sets", "Internet formats", f"Name a registered IANA character encoding ({DATE} snapshot).",
             "Every IANA Character Sets registry entry. Unique registered alias names are accepted.",
             records, IANA, popular="UTF-8|US-ASCII|ISO-8859-1|UTF-16|UTF-32|windows-1252|Shift_JIS|EUC-JP|Big5|GBK", key="KOI8-R")

    protocols = [Answer(item["Decimal"], "https://www.iana.org/assignments/protocol-numbers",
                        [item["Keyword"], item["Protocol"]])
                 for item in bank.csv("protocols") if item["Decimal"].isdigit() and (item["Keyword"] or item["Protocol"])
                 and not any(word in (item["Keyword"] + item["Protocol"]).lower()
                             for word in ("unassigned", "reserved", "experimentation", "deprecated"))]
    bank.add("iana-ip-protocols", "Networking", f"Give an assigned IP protocol number or name from IANA ({DATE} snapshot).",
             "Individual assigned entries, excluding reserved, deprecated, or experimental rows. Use a number or an unambiguous registered name.",
             protocols, IANA, popular="6|17|1|58|2|47|50|51|89|132", key="112")
    ports = [item for item in bank.csv("ports") if item["Service Name"] and item["Port Number"].isdigit()
             and 1 <= int(item["Port Number"]) <= 1023]
    for transport, anchors in [
        ("tcp", "http|https|ssh|ftp|smtp|telnet|domain|pop3|imap|ldap|nntp|gopher|rsync"),
        ("udp", "domain|bootps|bootpc|tftp|ntp|snmp|snmptrap|rip|syslog|isakmp|kerberos"),
    ]:
        rows = [Answer(row["Service Name"], "https://www.iana.org/assignments/service-names-port-numbers/")
                for row in ports if row["Transport Protocol"] == transport]
        bank.add("iana-" + transport + "-services", "Networking",
                 f"Name an IANA service name assigned a {transport.upper()} port from 1 to 1023 ({DATE} snapshot).",
                 "Use the service name. Every registered name with a single port in the stated range and transport.",
                 rows, IANA, popular=anchors)


def unicode_data(bank):
    unicode_url = "https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt"
    blocks_url = "https://www.unicode.org/Public/17.0.0/ucd/Blocks.txt"
    blocks = {}
    for line in bank.text("unicode-blocks").splitlines():
        if m := re.match(r"([0-9A-F]+)\.\.([0-9A-F]+); (.+)", line):
            blocks[m[3]] = (int(m[1], 16), int(m[2], 16))
    bank.plain("unicode-block-names", "Unicode", "Name a block in the Unicode 17.0 standard.",
               "All ranges with a name in the Unicode 17.0 Blocks registry.",
               blocks, blocks_url, UNICODE, popular="Basic Latin|Latin-1 Supplement|Greek and Coptic|Cyrillic|Arrows|Mathematical Operators|Emoticons|Box Drawing|Currency Symbols", key="Geometric Shapes Extended")
    controls = {}
    for line in bank.text("unicode-names").splitlines():
        if m := re.match(r"([0-9A-F]+);([^;]+);[^#]+", line):
            controls.setdefault(int(m[1], 16), []).append(m[2])
    data = [(int(fields[0], 16), fields[1]) for line in bank.text("unicode").splitlines() if (fields := line.split(";"))]
    for block, anchors in [
        ("Basic Latin", "SPACE|LATIN CAPITAL LETTER A|DIGIT ZERO|EXCLAMATION MARK|NUMBER SIGN|LINE FEED|LATIN SMALL LETTER A|DELETE|HYPHEN-MINUS|COMMERCIAL AT"),
        ("Latin-1 Supplement", "COPYRIGHT SIGN|REGISTERED SIGN|DEGREE SIGN|POUND SIGN|YEN SIGN|MULTIPLICATION SIGN|DIVISION SIGN|NO-BREAK SPACE"),
        ("Latin Extended-A", "LATIN SMALL LETTER L WITH STROKE|LATIN SMALL LETTER S WITH CARON|LATIN CAPITAL LETTER D WITH STROKE"),
        ("Greek and Coptic", "GREEK SMALL LETTER ALPHA|GREEK SMALL LETTER BETA|GREEK SMALL LETTER PI|GREEK SMALL LETTER OMEGA|GREEK CAPITAL LETTER DELTA"),
        ("Cyrillic", "CYRILLIC CAPITAL LETTER A|CYRILLIC SMALL LETTER A|CYRILLIC SMALL LETTER YA|CYRILLIC CAPITAL LETTER ZHE"),
        ("Mathematical Operators", "INFINITY|NOT EQUAL TO|LESS-THAN OR EQUAL TO|GREATER-THAN OR EQUAL TO|SQUARE ROOT|INTEGRAL|ELEMENT OF|SUMMATION"),
        ("Miscellaneous Symbols", "TELEPHONE SIGN|BLACK STAR|WHITE STAR|CHECK BALLOT BOX|SUN|CLOUD|UMBRELLA|SNOWMAN|BALLOT BOX"),
        ("Arrows", "LEFTWARDS ARROW|RIGHTWARDS ARROW|UPWARDS ARROW|DOWNWARDS ARROW|LEFT RIGHT ARROW|RIGHTWARDS DOUBLE ARROW"),
    ]:
        lo, hi = blocks[block]
        rows = []
        for code, name in data:
            if not lo <= code <= hi:
                continue
            aliases = list(controls.get(code, []))
            if name == "<control>" and aliases:
                name = aliases.pop(0)
            assert not name.startswith("<"), (block, name)
            char = chr(code)
            if char.isprintable() and char.strip():
                aliases.append(char)
            rows.append(Answer(name, unicode_url, [f"U+{code:04X}", *aliases]))
        slug = "ucd-" + re.sub(r"[^a-z0-9]+", "-", block.lower()).strip("-")
        bank.add(slug, "Character encoding", f"Give a Unicode 17.0 character in the {block} block.",
                 "Assigned characters only. Use the Unicode name or U+ code point. Unambiguous printable characters are accepted as shorthand.",
                 rows, UNICODE, popular=anchors)
    emoji_url = "https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt"
    lines = bank.text("emoji").splitlines()
    assert "# Version: 17.0" in lines
    groups = {}
    alt = {}
    group = None
    for line in lines:
        if line.startswith("# group: "):
            group = line.removeprefix("# group: ")
        elif m := re.match(r"([0-9A-F ]+);\s*(\S+)\s*#\s+(\S+)\s+E[\d.]+\s+(.*?)\s*$", line):
            code, status, glyph, name = m.groups()
            if any(codepoint in {"1F3FB", "1F3FC", "1F3FD", "1F3FE", "1F3FF"} for codepoint in code.split()):
                continue
            if status == "fully-qualified":
                groups.setdefault(group, []).append(Answer(name, emoji_url, [glyph]))
            else:
                alt.setdefault(name, []).append(glyph)
    for group, anchors in [
        ("Smileys & Emotion", "grinning face|face with tears of joy|red heart|smiling face|crying face|winking face|thinking face|skull"),
        ("People & Body", "thumbs up|thumbs down|clapping hands|folded hands|person running|person walking|waving hand|raised hand"),
        ("Animals & Nature", "dog|cat|lion|tiger|horse|cow|pig|monkey|rose|sunflower|deciduous tree|penguin"),
        ("Food & Drink", "red apple|banana|pizza|hamburger|spaghetti|cake|bread|hot beverage|grapes|lemon|watermelon"),
        ("Travel & Places", "automobile|airplane|train|ship|helicopter|bus|bicycle|house|hospital|mountain|rocket"),
        ("Objects", "laptop|desktop computer|keyboard|mobile phone|light bulb|wrench|hammer|battery|lock|key|books"),
        ("Symbols", "warning|no entry|check mark|cross mark|copyright|registered|infinity|recycling symbol|peace symbol"),
    ]:
        for row in groups[group]:
            row.aliases.extend(alt.get(row.name, []))
        slug = "emoji-" + re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        bank.add(slug, "Emoji and text", f"Name or enter a Unicode Emoji 17.0 emoji in {group}.",
                 "Every fully-qualified entry in that Unicode emoji-test group without a skin-tone modifier.",
                 groups[group], UNICODE, popular=anchors)
    entities_url = "https://html.spec.whatwg.org/multipage/named-characters.html"
    rows = (Answer(name, entities_url, [name[1:-1]]) for name in bank.json("entities") if name.endswith(";"))
    bank.add("html-entities", "HTML", f"Name a named HTML character reference from WHATWG ({DATE} snapshot).",
             "Every semicolon-terminated entity, with case as listed. Both &name; and the bare name work.",
             rows, "WHATWG HTML Living Standard; named reference identifiers",
             popular="&amp;|&lt;|&gt;|&quot;|&nbsp;|&apos;|&copy;|&reg;|&euro;|&mdash;|&hellip;", key="&frac58;", case_sensitive=True)


def exact_rules(bank):
    manual = "Deterministic enumeration of the stated rule"
    binary_doc = "https://docs.python.org/3.12/library/stdtypes.html#bitwise-operations-on-integer-types"
    base_doc = "https://docs.python.org/3.12/library/functions.html#int"
    specs = [
        ("byte-even-parity", "Binary representation", "Give an eight-bit binary string with an even number of 1s.",
         "Exactly eight digits, each 0 or 1. Leading zeros are part of the answer.",
         (f"{n:08b}" for n in range(256) if n.bit_count() % 2 == 0), binary_doc, "00000000|11111111|10101010|01010101|11000000|00000011|11110000", "10110100"),
        ("hex-two-digits", "Binary representation", "Give a two-digit hexadecimal byte whose first digit is smaller than its second.",
         "Both digits are hexadecimal, and a leading zero is allowed. 0x is an optional prefix.",
         (f"{number:02X}" for number in range(256) if number // 16 < number % 16), base_doc, "01|02|03|0A|09|12|23|3F", "7C"),
        ("nine-bit-multiple", "Binary representation", "Give a decimal multiple of 3 that fits in an unsigned nine-bit value.",
         "The inclusive interval is 0–511. Include zero.",
         range(0, 512, 3), binary_doc, "0|3|6|9|12|15|30|99|255|510", "381"),
        ("signed-byte", "Binary representation", "Give a negative integer that fits in a signed eight-bit two’s-complement value.",
         "Give the answer as a decimal integer.",
         range(-128, 0), binary_doc, "-1|-2|-3|-4|-10|-100|-127|-128", "-73"),
        ("mask-low-nibble", "Bitwise logic", "Give a byte X for which X AND 0x0F is nonzero.",
         "Enter X as a decimal integer from 0 through 255.",
         (n for n in range(256) if n & 15), binary_doc, "1|2|3|4|5|10|15|31|127|255", "169"),
        ("balanced-brackets", "Data structures", "Give a valid sequence of exactly six matching pairs of parentheses.",
         "Use only ( and ). Every prefix must have at least as many openings as closings.",
         ("".join(bits) for bits in itertools.product("()", repeat=12)
          if bits.count("(") == 6 and all(prefix.count("(") >= prefix.count(")")
          for prefix in itertools.accumulate(bits))), "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2010/",
         "()()()()()()|(((((())))))|((()))((()))|()((()))(())", "(()())(())()"),
        ("bst-root-four", "Data structures", "Give an insertion order for digits 1–7 that makes 4 the root of an empty, unbalanced BST.",
         "Type seven digits with no repeats or separators. There is no automatic balancing.",
         ("4" + "".join(rest) for rest in itertools.permutations("123567")),
         "https://opendatastructures.org/versions/edition-0.1c/ods-java/node38.html",
         "4123567|4765321|4261537|4213657|4567123", "4736152"),
        ("regex-string", "Text patterns", "Give a four-letter string over a, b, c, and d that contains at least one a.",
         "Exactly four lowercase letters from the given set.", ("".join(chars) for chars in itertools.product("abcd", repeat=4) if "a" in chars),
         "https://docs.python.org/3.12/library/re.html", "aaaa|abcd|aaab|aabb|abca|baaa|acdc", "dcab"),
        ("base64-one-byte", "Data encoding", "Give the canonical Base64 encoding of one byte, including the two = signs.",
         "Use RFC 4648's standard alphabet and zero pad bits. Enter the four-character result.",
         (base64.b64encode(bytes([n])).decode() for n in range(256)), "https://www.rfc-editor.org/rfc/rfc4648.html#section-4",
         "AA==|YQ==|QQ==|/w==|MA==|Zg==", "ng=="),
        ("private-ipv4-hosts", "Addressing", "Give a host address inside 192.168.1.0/24.",
         "Dotted-decimal IPv4, excluding the subnet’s network and broadcast addresses.",
         (f"192.168.1.{i}" for i in range(1, 255)), "https://www.rfc-editor.org/rfc/rfc1918.html",
         "192.168.1.1|192.168.1.2|192.168.1.10|192.168.1.100|192.168.1.254", "192.168.1.137"),
        ("unix-owner-write", "Operating systems", "Give a three-digit octal Unix permission mode where the owner can read and write.",
         "Exactly three digits 0–7. Owner execution and group/other bits can be set or unset.",
         (f"{a}{b}{c}" for a in (6, 7) for b in range(8) for c in range(8)), "https://www.gnu.org/software/coreutils/manual/html_node/Numeric-Modes.html",
         "644|600|755|777|700|664|666|750|640", "673"),
        ("private-ipv4-subnets", "Addressing", "Give a /24 subnet within 10.0.0.0/16, in CIDR notation.",
         "Use the subnet's network address followed by /24.",
         (f"10.0.{i}.0/24" for i in range(256)), "https://www.rfc-editor.org/rfc/rfc4632.html",
         "10.0.0.0/24|10.0.1.0/24|10.0.2.0/24|10.0.255.0/24|10.0.100.0/24", "10.0.147.0/24"),
        ("gregorian-leap", "Dates and time", "Give a Gregorian leap year from 1600 to 2100 inclusive.",
         "Use a four-digit year. Centuries must be divisible by 400.",
         (yr for yr in range(1600, 2101) if yr % 4 == 0 and (yr % 100 != 0 or yr % 400 == 0)),
         "https://docs.python.org/3.12/library/calendar.html#calendar.isleap", "2024|2000|2020|2016|2028|1996|1600|2096", "1776"),
        ("four-byte-alignment", "Computer systems", "Give a byte offset where a four-byte-aligned, four-byte value fits inside a 512-byte buffer.",
         "Enter the zero-based offset in decimal. All four bytes must fit.",
         range(0, 509, 4), "https://docs.kernel.org/core-api/unaligned-memory-access.html", "0|4|8|16|32|64|128|256|508", "356"),
        ("manhattan-grid", "Algorithms", "Give a point in a 16×16 grid within Manhattan distance 8 of (7,7).",
         "Each coordinate is an integer from 0 to 15. Use (x,y).",
         (f"({x},{y})" for x in range(16) for y in range(16) if abs(x - 7) + abs(y - 7) <= 8),
         "https://xlinux.nist.gov/dads/HTML/manhattanDistance.html", "(7,7)|(7,8)|(8,7)|(8,8)|(0,7)|(7,0)|(7,15)|(15,7)", "(3,11)"),
        ("byte-octal", "Data encoding", "Give an unsigned byte as a three-digit octal number.",
         "Exactly three octal digits, including leading zeros if needed.",
         (f"{n:03o}" for n in range(256)), base_doc, "000|001|007|010|100|177|377", "264"),
    ]
    for slug, cat, prompt, scope, names, url, anchors, featured in specs:
        rows = []
        for name in map(str, names):
            aliases = []
            if slug == "hex-two-digits":
                aliases.append("0x" + name)
            if slug == "manhattan-grid":
                aliases.append(name.replace(",", ", "))
            rows.append(Answer(name, url, aliases))
        bank.add(slug, cat, prompt, scope, rows, manual, popular=anchors, key=featured,
                 case_sensitive=slug in {"base64-one-byte", "regex-string"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, help="Directory containing files named by source manifest keys")
    parser.add_argument("--fetch", action="store_true", help="Fetch missing snapshots and verify their checksums")
    parser.add_argument("--out", type=Path, default=SEED / "curated_questions.json")
    parser.add_argument("--inspect", action="store_true", help="List candidate scopes and counts without writing")
    args = parser.parse_args()
    manifest = json.loads((SEED / "source_manifest.json").read_text(encoding="utf-8"))
    args.sources.mkdir(parents=True, exist_ok=True)
    for key, spec in manifest.items():
        file = args.sources / key
        if not file.exists() and args.fetch:
            subprocess.run(["curl", "-fLsS", "--max-time", "40", spec["url"], "-o", str(file)], check=True)
        if hashlib.sha256(file.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"Source snapshot {key} does not match its recorded checksum.")
    bank = Bank(args.sources, {key: spec["url"] for key, spec in manifest.items()})
    for group in (web, python, java, nodejs, tools, registries, unicode_data, exact_rules):
        group(bank)
    retired_candidates = {
        "curated-debian-mail", "curated-debian-comm", "curated-debian-electronics", "curated-debian-httpd",
        "curated-debian-web", "curated-debian-text", "curated-ucd-latin-extended-a", "curated-ucd-cyrillic",
        "curated-java-awt-types", "curated-emoji-people-body", "curated-debian-interpreters",
    }
    bank.questions = [question for question in bank.questions if question["slug"] not in retired_candidates]
    if args.inspect:
        for question in bank.questions:
            print(len(question["answers"]), question["slug"])
        print(f"Usable scopes: {len(bank.questions)}. Rejected scopes: {bank.skipped}")
        return
    assert len(bank.questions) == 100, (len(bank.questions), bank.skipped)
    # Keep one answer per line so targeted editorial adjustments are reviewable.
    with args.out.open("w", encoding="utf-8") as output:
        output.write("[\n")
        for index, question in enumerate(bank.questions):
            if index:
                output.write(",\n")
            fields = question.copy()
            answers = fields.pop("answers")
            output.write("  " + json.dumps(fields, ensure_ascii=False)[:-1] + ', "answers": [\n')
            output.write(",\n".join("    " + json.dumps(answer, ensure_ascii=False) for answer in answers))
            output.write("\n  ]}")
        output.write("\n]\n")


if __name__ == "__main__":
    main()
