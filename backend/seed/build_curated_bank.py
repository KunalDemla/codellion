"""Build the playable bank from pinned reference catalogs."""

import argparse
import builtins
import csv
import hashlib
import html
import inspect
import json
import keyword
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path

import yaml

SEED = Path(__file__).resolve().parent
sys.path.insert(0, str(SEED.parent))
from app.services.answer_validator import normalize_answer
from answer_aliases import additional_aliases
from named_prompts import extra_catalogs

POINTS = (10, 15, 30, 60, 85, 100)
BCD = "CC0-1.0 (MDN browser compatibility data)"
IANA = "IANA registry; factual identifiers"
PYTHON = "Python documentation and runtime; factual identifiers"
PY_DOCS = "https://docs.python.org/3.12/"
MDN = "https://developer.mozilla.org/docs/Web/"


@dataclass
class Answer:
    name: str
    url: str
    aliases: list[str] = field(default_factory=list)


class Bank:
    def __init__(self, folder):
        self.folder = folder
        self.questions = []
        self.slugs = set()

    def text(self, key):
        return (self.folder / key).read_text(encoding="utf-8")

    def json(self, key):
        return json.loads(self.text(key))

    def csv(self, key):
        return csv.DictReader(StringIO(self.text(key)))

    def add(self, slug, category, prompt, scope, rows, license_name, *, common, root=None, sensitive=False):
        if slug in self.slugs:
            raise ValueError(f"Duplicate question: {slug}")
        self.slugs.add(slug)

        def normalize(text):
            return normalize_answer(text, sensitive)

        by_name = {}
        for row in rows:
            name = normalize(row.name)
            if not name:
                raise ValueError(f"{slug}: blank answer")
            if name in by_name:
                by_name[name].aliases.extend(row.aliases)
            else:
                by_name[name] = row
        if len(by_name) < 11:
            raise ValueError(f"{slug}: only {len(by_name)} answers for six tiers")

        anchors = [normalize(value) for value in common.split("|")]
        missing = set(anchors) - by_name.keys()
        if missing:
            raise ValueError(f"{slug}: common answers absent from source: {sorted(missing)}")

        names = [name for name in by_name if name not in anchors]
        featured = normalize(root) if root else names[len(names) * 3 // 4]
        if featured not in names:
            raise ValueError(f"{slug}: Root Key is missing or marked common: {featured}")

        ordered = anchors + [name for name in names if name != featured]
        public = min(len(anchors), len(ordered) - 8)
        later = len(ordered) - public
        trick, user_space, privileged = (max(2, later * share // 10) for share in (2, 2, 3))
        kernel = later - trick - user_space - privileged
        tiers = [1] * public + [2] * trick + [3] * user_space + [4] * privileged + [5] * kernel + [6]
        source_alias_counts = Counter()
        for name, row in by_name.items():
            source_alias_counts.update({normalize(alias) for alias in row.aliases} - {name, ""})
        additions = additional_aliases(slug, by_name.values(), normalize)
        alias_counts = Counter()
        for candidates in additions.values():
            alias_counts.update({normalize(alias) for alias in candidates} - {""})

        answers = []
        for name, tier in zip(ordered + [featured], tiers, strict=True):
            row = by_name[name]
            aliases = {}
            for alias in row.aliases:
                token = normalize(alias)
                if token and not token.isdigit() and token not in by_name and source_alias_counts[token] == 1:
                    aliases.setdefault(token, alias)
            for alias in additions.get(name, []):
                token = normalize(alias)
                if (token and not token.isdigit() and token not in by_name
                        and token not in source_alias_counts and alias_counts[token] == 1):
                    aliases.setdefault(token, alias)
            answers.append({
                "canonical": row.name, "aliases": sorted(aliases.values(), key=str.casefold),
                "rarity_tier": tier, "points": POINTS[tier - 1],
                "source_url": row.url, "license_name": license_name,
            })
        self.questions.append({
            "slug": "curated-basics-" + slug,
            "category": {"slug": re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-"), "name": category},
            "prompt": prompt, "scope": scope, "allow_fuzzy": False,
            "case_sensitive": sensitive, "status": "approved", "answers": answers,
        })

    def plain(self, slug, category, prompt, scope, values, url, license_name, **kwargs):
        self.add(slug, category, prompt, scope, (Answer(str(x), url) for x in values), license_name, **kwargs)


def documented(entries):
    return {
        name: node for name, node in entries.items()
        if "__compat" in node and not node["__compat"].get("status", {}).get("deprecated", False)
    }


def reference(node, fallback):
    meta = node["__compat"]
    value = meta.get("mdn_url") or meta.get("spec_url") or fallback
    return value[0] if isinstance(value, list) else value


def web(bank):
    data = bank.json("bcd")
    assert data["__meta"]["version"] == "8.1.10"
    html_elements = MDN + "HTML/Reference/Elements"
    bank.add("html-elements", "HTML", "Name an HTML element.",
             "Use a current element in the MDN list. A bare name or an opening tag works.",
             (Answer(name, reference(node, html_elements), [f"<{name}>"])
              for name, node in documented(data["html"]["elements"]).items()),
             BCD, common="div|p|a|span|img|input|button|h1|form|table", root="wbr")
    attributes = {}
    for group in [data["html"]["global_attributes"], *data["html"]["elements"].values()]:
        for name, node in documented(group).items():
            meta = node["__compat"]
            url = meta.get("mdn_url", "")
            spec = meta.get("spec_url", [])
            refs = [spec] if isinstance(spec, str) else spec
            if name in data["html"]["global_attributes"] or "#attr-" in url or any("#attr-" in ref for ref in refs):
                attributes.setdefault(name, Answer(name, reference(node, html_elements)))
    inputs = documented(data["html"]["elements"]["input"])
    bank.plain("html-input-types", "HTML", "Name a type of HTML input.",
               "Give a current type value for the input element, such as a field, picker, or button.",
               (name.removeprefix("type_") for name in inputs if name.startswith("type_")),
               MDN + "HTML/Reference/Elements/input", BCD,
               common="text|password|email|number|checkbox|radio|file|date|submit", root="datetime-local")
    bank.add("html-attributes", "HTML", "Name an HTML attribute.",
             "Use an attribute listed by MDN for an element or for all elements. Attribute names only.",
             attributes.values(), BCD, common="id|class|href|src|alt|style|title|type|name|value", root="inputmode")
    css = documented(data["css"]["properties"])
    bank.add("css-properties", "CSS", "Name a CSS property.",
             "Use a current property in the MDN list. Custom properties are excluded.",
             (Answer(name, reference(node, MDN + "CSS/Reference/Properties"))
              for name, node in css.items() if not name.startswith("--")),
             BCD, common="color|display|margin|padding|width|height|font-size|background|opacity|border",
             root="scroll-margin-inline")
    colors = re.findall(r"<th scope=row><dfn>([a-z]+)</dfn><td>#[0-9a-f]{6}", bank.text("css-colors"), re.I)
    assert len(colors) == 148
    bank.plain("css-colors", "CSS", "Name a CSS color keyword.",
               "Use one of the 148 CSS named colors. Hex codes and functional colors are separate.",
               colors, "https://drafts.csswg.org/css-color-4/#named-colors", "W3C standard; color identifiers",
               common="red|blue|green|white|black|yellow|orange|pink|purple|gray", root="papayawhip")
    selectors = documented(data["css"]["selectors"])
    pseudo = []
    for name, node in selectors.items():
        link = reference(node, MDN + "CSS/Reference/Selectors")
        if isinstance(link, str) and link.rsplit("/", 1)[-1].startswith(":") and not link.rsplit("/", 1)[-1].startswith("::"):
            pseudo.append(Answer(name, link, [":" + name, ":" + name + "()"]))
    bank.add("css-pseudo-classes", "CSS", "Name a CSS pseudo-class.",
             "Use the name, with or without the leading colon. Current pseudo-classes in MDN.",
             pseudo, BCD, common="hover|active|focus|checked|disabled|first-child|last-child|not", root="placeholder-shown")
    objects = documented(data["javascript"]["builtins"])
    js_ref = MDN + "JavaScript/Reference/Global_Objects"
    identifiers = []
    for name, node in objects.items():
        link = reference(node, js_ref)
        if link.startswith(js_ref + "/"):
            identifiers.append(Answer(name, link))
    bank.add("js-globals", "JavaScript", "Name a built-in JavaScript global.",
             "Use an unqualified standard global from MDN, such as a constructor, function, or value. Browser globals are separate.",
             identifiers, BCD, common="Array|Object|String|Number|Math|Date|JSON|Promise|Map|Set|parseInt|undefined", root="AggregateError")
    methods = []
    for owner, obj in objects.items():
        for name, node in documented(obj).items():
            link = node["__compat"].get("mdn_url", "")
            if not link.startswith(js_ref + "/") or link.rsplit("/", 1)[-1] != name:
                continue
            spec = node["__compat"].get("spec_url", [])
            refs = [spec] if isinstance(spec, str) else spec
            if any("sec-" in entry for entry in refs) and name not in {
                "length", "name", "prototype", "constructor", "size", "buffer", "byteOffset", "byteLength",
            } and not name.isupper():
                methods.append(Answer(name, link, [f"{owner}.{name}", f"{name}()"]))
    bank.add("js-members", "JavaScript", "Name a method or property on a built-in JavaScript object.",
             "Use an MDN-listed member name. Shared names count once. Generic properties such as length, name, and size are excluded.",
             methods, BCD, common="map|filter|reduce|push|pop|split|join|slice|parse|stringify|keys|random", root="flatMap")
    dom_events = {}
    for interface, node in data["api"].items():
        for event, entry in documented(node).items():
            if event.endswith("_event"):
                name = event.removesuffix("_event")
                dom_events.setdefault(name, Answer(name, reference(entry, MDN + "Events"), ["on" + name]))
    bank.add("dom-events", "Web APIs", "Name a browser event.",
             "Use a current DOM event in MDN, with or without its on prefix.",
             dom_events.values(), BCD, common="click|input|submit|load|focus|blur|keydown|change|scroll", root="hashchange")


def languages(bank):
    meta = yaml.safe_load(bank.text("linguist"))
    linguist = "https://github.com/github-linguist/linguist/blob/cfd7a0113aa1efab99faeff38756f0ed4d48add8/lib/linguist/languages.yml"
    for kind, slug, prompt, common, root in [
        ("programming", "programming-languages", "Name a programming language.", "Python|Java|JavaScript|TypeScript|C|C++|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|R|Lua", "Forth"),
        ("markup", "markup-languages", "Name a markup or document-formatting language.", "HTML|Markdown|TeX|AsciiDoc|reStructuredText|XML", "Haml"),
        ("data", "data-formats", "Name a text format used to store data or configuration.", "JSON|YAML|CSV|TOML|XML|INI|TSV", None),
    ]:
        bank.add(slug, "Languages" if kind != "data" else "Data formats", prompt,
                 ("Uses Linguist’s markup list and common document formats such as Markdown and XML. Listed aliases are accepted."
                  if kind == "markup" else "Uses GitHub Linguist’s " + kind + " list. Listed aliases are accepted."),
                 (Answer(name, linguist, detail.get("aliases", [])) for name, detail in meta.items()
                  if detail["type"] == kind or (kind == "markup" and (name in {"Markdown", "AsciiDoc", "reStructuredText", "Textile", "Org", "Wikitext", "XML"}))),
                 "MIT (GitHub Linguist metadata)", common=common, root=root)
    bank.add("source-extensions", "File formats", "Name a source-code file extension.",
             "Use an extension GitHub Linguist associates with a programming language. The leading dot is optional.",
             (Answer(ext, linguist, [ext.removeprefix(".")]) for details in meta.values()
              if details["type"] == "programming" for ext in details.get("extensions", [])),
             "MIT (GitHub Linguist metadata)", common=".py|.js|.ts|.java|.c|.cpp|.go|.rs|.rb|.php", root=".f90")

    bank.plain("python-modules", "Python", "Name a Python standard library module.",
               "Use a top-level name from Python’s standard library. Third-party packages are separate.",
               sorted(sys.stdlib_module_names), PY_DOCS + "library/sys.html#sys.stdlib_module_names", PYTHON,
               common="math|random|os|sys|json|re|time|datetime|collections|pathlib|itertools|statistics", root="bisect")
    functions = [(name, getattr(builtins, name)) for name in dir(builtins)]
    bank.add("python-builtins", "Python", "Name a built-in Python function.",
             "Use a function available without an import. Data types are separate. Parentheses are optional.",
             (Answer(name, PY_DOCS + "library/functions.html", [name + "()"])
              for name, obj in functions if inspect.isbuiltin(obj)),
             PYTHON, common="print|len|input|sum|sorted|abs|max|min|open", root="divmod", sensitive=True)
    bank.plain("python-types", "Python", "Name a built-in Python data type.",
               "Use a non-exception class available without an import.",
               (name for name, obj in functions if isinstance(obj, type) and not issubclass(obj, BaseException)),
               PY_DOCS + "library/stdtypes.html", PYTHON, common="int|float|str|bool|list|tuple|dict|set", root="memoryview",
               sensitive=True)
    bank.plain("python-keywords", "Python", "Name a Python keyword.",
               "Use a reserved Python keyword. Context-dependent soft keywords are separate.",
               keyword.kwlist, PY_DOCS + "reference/lexical_analysis.html#keywords", PYTHON,
               common="if|else|for|while|import|return|def|class|True|False", root="nonlocal", sensitive=True)
    bank.plain("python-exceptions", "Python", "Name a built-in Python exception.",
               "Give the name of an exception or warning class available without an import.",
               (name for name, obj in functions if isinstance(obj, type) and issubclass(obj, BaseException)),
               PY_DOCS + "library/exceptions.html", PYTHON,
               common="TypeError|ValueError|NameError|KeyError|IndexError|SyntaxError|ZeroDivisionError|ImportError",
               root="UnboundLocalError", sensitive=True)


def everyday_tools(bank):
    ranking = bank.text("database-ranking")
    aliases = {
        "PostgreSQL": ["Postgres"], "Microsoft SQL Server": ["SQL Server", "MSSQL"],
        "Oracle": ["Oracle Database", "Oracle DB"], "SQLite": ["SQLite3"],
        "Apache Cassandra": ["Cassandra"],
    }
    databases = []
    for link, label in re.findall(r'<th class="pad-l"><a href="(https://db-engines\.com/en/system/[^"]+)">(.*?)</a>', ranking):
        name = html.unescape(label.split("<", 1)[0]).strip()
        databases.append(Answer(name, link, aliases.get(name, [])))
    size = int(re.search(r"popularity of (\d+) database management systems", ranking)[1])
    assert len(databases) == size
    bank.add("database-engines", "Databases", "Name a database engine.",
             "Use an engine listed by DB-Engines. Its November 2026 ranking defines the complete answer list.",
             databases, "DB-Engines ranking; product names",
             common="MySQL|PostgreSQL|SQLite|MongoDB|Redis|Oracle|Microsoft SQL Server|MariaDB|Elasticsearch|Apache Cassandra",
             root="Firebird")
    keys = re.findall(r"<li>([A-Z_]+)</li>", bank.text("sqlite"))
    assert len(keys) == 147
    bank.plain("sql-keywords", "SQL", "Name a SQL keyword.",
               "Use one of the keywords in SQLite’s full SQL keyword list. Keyword phrases are separate.",
               keys, "https://www.sqlite.org/lang_keywords.html", "SQLite keyword identifiers",
               common="SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|TABLE|JOIN|ORDER|GROUP|LIMIT|HAVING",
               root="PRECEDING")
    functions = re.findall(r"<li><a href='lang_corefunc.html#([a-z0-9_]+)'>([a-z0-9_]+)\(", bank.text("sqlite-functions"))
    bank.add("sql-functions", "SQL", "Name a built-in SQLite function.",
             "Use a scalar function from SQLite’s core function list. Parentheses are optional.",
             (Answer(name, "https://www.sqlite.org/lang_corefunc.html#" + anchor, [name + "()"])
              for anchor, name in functions),
             "SQLite function identifiers", common="abs|length|lower|upper|round|coalesce|replace|substr|random|trim",
             root="nullif")
    aggregate = re.findall(r"<li><a href='lang_aggfunc.html#([a-z0-9_]+)'>([a-z0-9_]+)\(", bank.text("sqlite-aggregates"))
    bank.add("sql-aggregates", "SQL", "Name a SQL aggregate function.",
             "Use a built-in aggregate in SQLite’s aggregate-function list. Parentheses are optional.",
             (Answer(name, "https://www.sqlite.org/lang_aggfunc.html#" + link, [name + "()"]) for link, name in aggregate),
             "SQLite function identifiers", common="count|sum|avg|max|min", root="group_concat")
    types_page = bank.text("postgres-types").split('summary="Data Types"')[1].split("</table>")[0]
    pg_types = []
    for row in re.findall(r"<tr>(.*?)</tr>", types_page, re.S):
        cells = re.findall(r"<td>(.*?)</td>", row, re.S)
        if len(cells) < 2:
            continue
        names = re.findall(r'<code class="type">(.*?)</code>', cells[0])
        if names:
            aliases = re.findall(r'<code class="type">(.*?)</code>', cells[1])
            base_name = html.unescape(names[0].split(" [", 1)[0])
            pg_types.append(Answer(base_name, "https://www.postgresql.org/docs/17/datatype.html",
                                   [html.unescape(name.split(" [", 1)[0]) for name in aliases]))
    bank.add("sql-data-types", "SQL", "Name a SQL data type.",
             "Use a type or alias from PostgreSQL’s built-in data type table.",
             pg_types, "PostgreSQL documentation; type identifiers",
             common="integer|character varying|text|boolean|date|numeric|real|smallint", root="inet")
    tldr = bank.json("tldr")
    assert not tldr["truncated"]
    names = {}
    for item in tldr["tree"]:
        path = item["path"]
        match = re.fullmatch(r"pages/(?:common|linux)/([a-zA-Z0-9_.+-]+)\.md", path)
        if match and not match[1].isdigit():
            name = match[1]
            names.setdefault(name, Answer(name, "https://github.com/tldr-pages/tldr/blob/" + tldr["sha"] + "/" + path))
    bank.add("shell-commands", "Command line", "Name a command you can run in a Linux terminal.",
             "Use a command name from the Linux or common tldr pages. Leave out flags, arguments, and all-number names.",
             names.values(), "MIT (tldr-pages); command names",
             common="ls|cd|mkdir|pwd|cat|echo|rm|cp|mv|grep|find|touch|chmod|curl|git", root="xargs")
    windows = [
        Answer(match[1], "https://github.com/tldr-pages/tldr/blob/" + tldr["sha"] + "/" + item["path"])
        for item in tldr["tree"] if (match := re.fullmatch(r"pages/windows/([a-zA-Z0-9_.+-]+)\.md", item["path"]))
    ]
    bank.add("windows-commands", "Command line", "Name a Windows terminal command.",
             "Use a standalone command in the Windows tldr pages. Leave out any arguments.",
             windows, "MIT (tldr-pages); command names",
             common="dir|cd|copy|ipconfig|tasklist|ping", root="robocopy")
    bank.add("git-commands", "Version control", "Name a Git command.",
             "Use a command from Git’s command list. Give the subcommand, with or without git in front.",
             (Answer(line.split()[0][4:], "https://git-scm.com/docs/" + line.split()[0],
                     ["git " + line.split()[0][4:], line.split()[0]])
              for line in bank.text("git").splitlines() if re.match(r"^git-[a-z0-9-]+\s", line)),
             "Git command identifiers",
             common="add|commit|status|clone|init|push|pull|fetch|log|diff|merge|rebase|branch|checkout",
             root="bisect")
    licenses = bank.json("license")["licenses"]
    bank.add("software-licenses", "Software projects", "Name an open-source license.",
             "Use the name or ID of a current SPDX license that is approved by the Open Source Initiative.",
             (Answer(item["licenseId"], item["reference"], [item["name"]])
              for item in licenses if item.get("isOsiApproved") and not item["isDeprecatedLicenseId"]),
             "CC0-1.0 (SPDX list metadata)",
             common="MIT|Apache-2.0|GPL-3.0-only|GPL-2.0-only|BSD-3-Clause|BSD-2-Clause|MPL-2.0|ISC",
             root="Artistic-2.0")

    pairs = re.findall(r'\{"([\w]+)", "([\w]+)"\},', bank.text("go-platforms").split("var distInfo")[0])
    operating_systems = {
        "darwin": ["macOS", "Mac OS", "OS X"], "plan9": ["Plan 9"],
        "wasip1": ["WASI"], "js": ["JavaScript"],
    }
    architectures = {
        "amd64": ["x86-64", "x86_64", "x64"], "386": ["i386", "32-bit x86", "Intel 386"],
        "arm64": ["AArch64"], "wasm": ["WebAssembly"], "ppc64": ["PowerPC64", "PowerPC 64"],
        "s390x": ["IBM Z"], "riscv64": ["RISC-V 64", "RISC-V"],
    }
    for slug, column, prompt, scope, aliases, common, root in [
        ("target-platforms", 0, "Name an operating system.",
         "Use a Go target operating system or runtime, such as Windows. Platform names and GOOS values work.",
         operating_systems, "linux|windows|darwin|android|ios|freebsd", "plan9"),
        ("cpu-architectures", 1, "Name a CPU or virtual machine architecture.",
         "Use an architecture from Go’s target list. Use the architecture name. Alphabetic GOARCH names also work.",
         architectures, "amd64|x86|arm|arm64|wasm|riscv64", "s390x"),
    ]:
        bank.add(slug, "Computer systems", prompt, scope,
                 (Answer("x86" if name == "386" else name,
                         "https://github.com/golang/go/blob/go1.24.0/src/internal/platform/zosarch.go", aliases.get(name, []))
                  for name in sorted({pair[column] for pair in pairs})),
                 "BSD-3-Clause (Go); target identifiers", common=common, root=root)


def internet(bank):
    iana = "https://www.iana.org/assignments/"
    status = []
    reason_aliases = {
        "OK": ["Success"],
        "Found": ["Moved Temporarily"],
        "Not Found": ["Page Not Found"],
        "Content Too Large": ["Payload Too Large", "Request Entity Too Large"],
        "Unprocessable Content": ["Unprocessable Entity"],
    }
    for row in bank.csv("http-status"):
        code, reason = row["Value"], row["Description"]
        if code.isdigit() and reason not in {"Unassigned", "Reserved"} and not reason.startswith("("):
            reason = re.sub(r" \(TEMPORARY.*$", "", reason)
            status.append(Answer(reason, iana + "http-status-codes", reason_aliases.get(reason, [])))
    status.append(Answer("I'm a teapot", "https://www.rfc-editor.org/rfc/rfc2324.html#section-2.3.2",
                         ["I’m a teapot", "teapot"]))
    bank.add("http-status-names", "HTTP", "Name an HTTP response status.",
             "Give its reason phrase, such as Not Found. Named IANA statuses and the historical teapot status count.",
             status, IANA,
             common="OK|Not Found|Internal Server Error|Moved Permanently|Forbidden|Unauthorized|Created|No Content|Bad Request|Found|Service Unavailable|I'm a teapot",
             root="IM Used")
    bank.plain("http-methods", "HTTP", "Name an HTTP request method.",
               "Use a method in IANA’s registry. The method name is enough.",
               (row["Method Name"] for row in bank.csv("http-methods")),
               iana + "http-methods", IANA, common="GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS", root="LOCK")
    bank.plain("http-headers", "HTTP", "Name an HTTP header.",
               "Use a permanent or provisional field name in IANA’s HTTP registry.",
               (row["Field Name"] for row in bank.csv("http-fields") if row["Status"] in {"permanent", "provisional"}),
               iana + "http-fields", IANA,
               common="Accept|Content-Type|Host|Authorization|User-Agent|Cookie|Set-Cookie|Content-Length|Cache-Control|Location",
               root="If-None-Match")
    bank.add("uri-schemes", "Networking", "Name a URL scheme.",
             "Give the part before the first colon. Permanent and provisional schemes registered with IANA count.",
             (Answer(row["URI Scheme"], iana + "uri-schemes", [row["URI Scheme"] + ":", row["URI Scheme"] + "://"])
              for row in bank.csv("uri-schemes") if row["Status"] in {"Permanent", "Provisional"} and row["URI Scheme"]),
             IANA, common="http|https|file|ftp|mailto|data|ws|wss|tel", root="magnet")
    ports = [row for row in bank.csv("ports") if row["Service Name"] and row["Port Number"].isdigit()]
    aliases = {"domain": ["DNS"], "bootps": ["DHCP"], "https": ["HTTP over TLS"],
               "http": ["HTTP/1.1"], "secure-mqtt": ["MQTT over TLS"]}
    bank.add("network-services", "Networking", "Name a network service or protocol that uses an assigned port.",
             "Use a service name in IANA’s TCP or UDP port registry. Established abbreviations such as DNS also count.",
             (Answer(row["Service Name"], iana + "service-names-port-numbers", aliases.get(row["Service Name"], []))
              for row in ports if row["Transport Protocol"] in {"tcp", "udp"}),
             IANA, common="http|https|ssh|ftp|domain|smtp|telnet|imap|pop3|ntp|snmp", root="gopher")
    bank.add("character-encodings", "Text and encoding", "Name a character encoding.",
             "Use a name or alias in IANA’s character set registry.",
             (Answer(row["Preferred MIME Name"] or row["Name"], iana + "character-sets",
                     [row["Name"], *row["Aliases"].split()])
              for row in bank.csv("charsets")),
             IANA, common="UTF-8|US-ASCII|ISO-8859-1|UTF-16|UTF-32|windows-1252|Shift_JIS|EUC-JP|Big5",
             root="KOI8-R")
    domains = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", bank.text("dns-root"), re.S):
        match = re.search(r'/domains/root/db/[^"\']+["\']>\s*(\.[^<\s]+)', row)
        if match and "domain-country-code." in row:
            name = html.unescape(match[1])
            domains.append(Answer(name, "https://www.iana.org/domains/root/db", [name[1:]]))
    bank.add("country-domains", "Networking", "Name a country-code top-level domain.",
             "Use a country or territory suffix listed by IANA. The leading dot is optional.",
             domains, IANA, common=".in|.uk|.us|.ca|.de|.au|.jp|.fr|.cn|.io", root=".tv")


def files(bank):
    mime = bank.json("mime-db")
    source = "https://github.com/jshttp/mime-db/blob/v1.54.0/db.json"
    groups = {
        "images": lambda name: name.startswith("image/"),
        "audio": lambda name: name.startswith("audio/"),
        "video": lambda name: name.startswith("video/"),
        "documents": lambda name: name.startswith(("text/", "application/vnd.ms-", "application/vnd.openxmlformats-"))
        or name in {"application/pdf", "application/rtf", "application/epub+zip"},
    }
    for group, title, common, root in [
        ("images", "an image", ".png|.jpg|.jpeg|.gif|.webp|.bmp|.svg|.ico|.tiff", ".avif"),
        ("audio", "an audio", ".mp3|.wav|.aac|.flac|.ogg|.m4a|.opus|.mid", ".caf"),
        ("video", "a video", ".mp4|.avi|.mov|.mkv|.webm|.mpeg|.m4v|.wmv", ".ogv"),
        ("documents", "a text or document", ".txt|.csv|.html|.md|.pdf|.docx|.xlsx|.pptx|.rtf", ".epub"),
    ]:
        bank.add(group + "-extensions", "File formats", f"Name {title} file extension.",
                 f"Use an extension associated with {title} media type in mime-db. The leading dot is optional.",
                 (Answer("." + ext, source, [ext]) for name, record in mime.items() if groups[group](name)
                  for ext in record.get("extensions", [])), "MIT (mime-db metadata)", common=common, root=root)
    media = [
        Answer(name, "https://www.iana.org/assignments/media-types/" + "#" + kind)
        for kind in ("image", "audio", "video", "application", "text")
        for item in bank.csv(kind)
        for name in [kind + "/" + item["Name"].split(" (", 1)[0]]
    ]
    bank.add("media-types", "Internet formats", "Name a MIME type.",
             "Use type/subtype from IANA’s text, image, audio, video, or application registries.",
             media, IANA, common="text/plain|text/html|application/json|image/png|image/jpeg|video/mp4|application/pdf|text/css|audio/mpeg",
             root="application/wasm")


def algorithms(bank):
    base = "https://xlinux.nist.gov/dads/"
    for slug, page, index, category, prompt, common, root in [
        ("data-structures", "nist-types", "S", "Data structures", "Name a data structure.",
         "array|stack|queue|linked list|hash table|binary tree|binary search tree|heap|trie", "skip list"),
        ("sorting-algorithms", "nist-areas", "sort", "Algorithms", "Name a sorting algorithm.",
         "bubble sort|quicksort|merge sort|insertion sort|selection sort|heapsort|radix sort|counting sort", "gnome sort"),
        ("search-algorithms", "nist-areas", "search", "Algorithms", "Name a search algorithm.",
         "binary search|linear search|breadth-first search|depth-first search|jump search", "Aho-Corasick"),
    ]:
        section = bank.text(page).split(f'<h2><a name="{index}">')[1].split("</ul>", 1)[0]
        if index == "search":
            section += '<li><a href="HTML/breadthfirst.html">breadth-first search</a> [<strong>A</strong>]</li>\n'
            section += '<li><a href="HTML/depthfirst.html">depth-first search</a> [<strong>A</strong>]</li>\n'
        by_reference = {}
        anchors = common.split("|")
        for url, label, kind in re.findall(
            r'<li><a href="(HTML/[^"]+)">(.*?)</a>(?: \[<strong>([A-Z])</strong>\])?</li>', section
        ):
            if page == "nist-areas" and kind != "A":
                continue
            name = html.unescape(re.sub("<[^>]+>", "", label))
            aliases = [name.replace("-", " "), name.replace(" ", "")]
            known = {"hash table": ["hashmap", "hash map"], "binary search tree": ["BST"],
                     "quicksort": ["quick sort"], "heapsort": ["heap sort"],
                     "breadth-first search": ["BFS"], "depth-first search": ["DFS"]}
            row = by_reference.get(url)
            if row and name not in anchors:
                row.aliases.extend([name, *aliases, *known.get(name, [])])
            else:
                existing = [row.name, *row.aliases] if row else []
                by_reference[url] = Answer(name, base + url, existing + aliases + known.get(name, []))
        scope = ("Use a structure in the NIST Dictionary of Algorithms and Data Structures."
                 if page == "nist-types" else
                 "Use an algorithm from NIST’s Searching index or a standard breadth-first or depth-first search."
                 if index == "search" else "Use a named sorting algorithm in the NIST sorting index.")
        bank.add(slug, category, prompt, scope, by_reference.values(), "NIST DADS; factual names", common=common, root=root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--out", type=Path, default=SEED / "curated_questions.json")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Use Python 3.12 to reproduce the Python answer sets.")
    manifest = json.loads((SEED / "source_manifest.json").read_text(encoding="utf-8"))
    args.sources.mkdir(parents=True, exist_ok=True)
    for name, spec in manifest.items():
        path = args.sources / name
        if args.fetch and not path.exists():
            subprocess.run(["curl", "-fLsS", "--max-time", "40", spec["url"], "-o", str(path)], check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"{name} does not match its source checksum")

    bank = Bank(args.sources)
    for group in (web, languages, everyday_tools, internet, files, algorithms):
        group(bank)
    extra_catalogs(bank, Answer)
    if args.inspect:
        for question in bank.questions:
            print(f"{len(question['answers']):5}  {question['prompt']}")
        print(f"{len(bank.questions)} questions")
        return
    assert len(bank.questions) == 100, len(bank.questions)
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
