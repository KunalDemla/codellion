"""Named answers for familiar programming, systems, and tooling prompts."""

import html
import re
import tarfile
from urllib.parse import urljoin
from xml.etree import ElementTree

import yaml

from catalog_aliases import bcd_aliases, domain_aliases, js_member_aliases, nist_aliases, registered_expansion


MDN = "https://developer.mozilla.org/docs/Web/"
PYTHON = "https://docs.python.org/3.12/library/"
IANA = "https://www.iana.org/assignments/"
NIST = "https://xlinux.nist.gov/dads/"
BCD = "CC0-1.0 (MDN browser compatibility data)"
IDENTIFIERS = "Primary reference; factual identifiers"


def names_in_pre(text):
    pre = re.search(r"<pre[^>]*>(.*?)</pre>", text, re.S)[1]
    return html.unescape(re.sub(r"<[^>]+>", " ", pre)).split()


def ready(entry):
    status = entry.get("__compat", {}).get("status", {})
    return bool(status) and not status.get("deprecated") and not status.get("experimental")


def web(bank, answer_type):
    bcd = bank.json("bcd")
    browsers = bcd["browsers"]
    engines = {"bun", "deno", "nodejs", "oculus", "quest"}
    aliases = {
        "Chrome": ["Google Chrome"], "Edge": ["Microsoft Edge"], "Firefox": ["Mozilla Firefox"],
        "Safari": ["Apple Safari"], "Internet Explorer": ["IE"], "Opera": ["Opera Browser"],
    }
    additional = {
        "Brave": ("https://brave.com/download/", ["Brave Browser"]),
        "Chromium": ("https://www.chromium.org/", []),
        "Tor Browser": ("https://www.torproject.org/download/", ["Tor"]),
        "Vivaldi": ("https://vivaldi.com/", []),
        "DuckDuckGo Browser": ("https://duckduckgo.com/app", ["DuckDuckGo"]),
        "Arc": ("https://arc.net/", ["Arc Browser"]),
    }
    rows = [
        answer_type(node["name"], node.get("website") or MDN, aliases.get(node["name"], []))
        for key, node in browsers.items() if key not in engines
    ]
    rows.extend(answer_type(name, url, variants) for name, (url, variants) in additional.items())
    bank.add("web-browsers", "Web browsers", "Name a web browser.",
             "Use MDN’s desktop or mobile list, plus Brave, Chromium, Tor Browser, Vivaldi, DuckDuckGo Browser, and Arc.",
             rows, BCD, common="Chrome|Firefox|Safari|Edge|Opera|Internet Explorer|Brave", root="Samsung Browser")


    js = bcd["javascript"]["builtins"]
    for owner, anchors, featured in [
        ("Array", "map|filter|push|pop|reduce|forEach|slice|find|sort|length", "toSpliced"),
        ("String", "split|length|trim|slice|replace|substring|includes|toUpperCase|toLowerCase", "normalize"),
        ("Math", "random|floor|ceil|round|abs|max|min|sqrt|pow|PI", "hypot"),
        ("Date", "now|getTime|getFullYear|getMonth|getDate|toISOString|parse|toString", "getTimezoneOffset"),
    ]:
        source = MDN + "JavaScript/Reference/Global_Objects/" + owner
        rows = []
        for name, entry in js[owner].items():
            if not ready(entry):
                continue
            link = entry["__compat"].get("mdn_url", "")
            if not link.startswith(source + "/") or link.rsplit("/", 1)[-1] != name:
                continue
            variants = list(js_member_aliases(owner, name, entry))
            if owner in {"Array", "String", "Date"}:
                variants.append(f"{owner}.prototype.{name}")
            rows.append(answer_type(name, link, variants))
        bank.add("js-" + owner.lower() + "-members", "JavaScript", f"Name a JavaScript {owner} method or property.",
                 f"Use a member in MDN’s {owner} reference. Static and instance members count.",
                 rows, BCD, common=anchors, root=featured)

    pseudo = []
    for name, entry in bcd["css"]["selectors"].items():
        if ready(entry):
            url = entry["__compat"].get("mdn_url", "")
            if url.rsplit("/", 1)[-1].startswith("::"):
                pseudo.append(answer_type(name, url, ["::" + name, "::" + name + "()", *bcd_aliases(name, entry)]))
    bank.add("css-pseudo-elements", "CSS", "Name a CSS pseudo-element.",
             "Use a current pseudo-element in MDN. The double colon is optional.", pseudo, BCD,
             common="before|after|first-letter|first-line|selection|placeholder|marker", root="file-selector-button")

    functions = re.findall(
        r'<a href="(/en-US/docs/Web/CSS/Reference/Values/[^"]+)"><code>([a-z0-9_-]+)\(\)</code>',
        bank.text("css-functions"),
    )
    bank.add("css-functions", "CSS", "Name a CSS function.",
             "Use a function in MDN’s CSS value reference, with or without parentheses.",
             (answer_type(name, "https://developer.mozilla.org" + link, [name + "()"]) for link, name in functions),
             IDENTIFIERS, common="calc|var|rgb|hsl|url|linear-gradient|clamp|min|max", root="color-mix")

    roles = re.findall(r'href="(/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/([a-z]+)_role)"',
                       bank.text("aria-roles"))
    bank.add("aria-roles", "Accessibility", "Name an ARIA role.",
             "Use a role in MDN’s reference for accessible web interfaces.",
             (answer_type(name, "https://developer.mozilla.org" + link) for link, name in roles),
             IDENTIFIERS, common="button|link|heading|dialog|checkbox|navigation|alert|list", root="status")

    dom = bank.text("ts-dom")
    methods = {}
    for owner in ("Document", "Element", "Node", "EventTarget", "ParentNode", "ChildNode", "NonElementParentNode"):
        section = re.search(rf"^interface {owner}\b[^{{]*\{{\n(.*?)^\}}", dom, re.M | re.S)[1]
        for name in re.findall(r"^    (\w+)(?:<[^\n]*?>)?\(", section, re.M):
            if name not in methods:
                methods[name] = answer_type(name, MDN + "API/" + owner + "/" + name, [name + "()"])
            qualified = owner + "." + name
            methods[name].aliases.extend((qualified, qualified + "()"))
    bank.add("dom-methods", "Web APIs", "Name a DOM method for working with a page.",
             "Use a method from the standard DOM node, element, document, or event-target interfaces, including their node mixins.",
             methods.values(), IDENTIFIERS,
             common="querySelector|querySelectorAll|getElementById|createElement|appendChild|removeChild|addEventListener|setAttribute|closest",
             root="compareDocumentPosition")


def languages(bank, answer_type):
    for owner, native, anchors, featured in [
        ("list", list, "append|pop|sort|reverse|extend|remove|insert", "copy"),
        ("dict", dict, "get|keys|values|items|update|pop|clear", "fromkeys"),
        ("str", str, "split|join|strip|lower|upper|replace|startswith|endswith|find", "casefold"),
        ("set", set, "add|remove|discard|union|intersection|difference|clear", "symmetric_difference_update"),
    ]:
        bank.add(f"python-{owner}-methods", "Python", f"Name a built-in Python {owner} method.",
                 f"Use a public method on Python’s {owner} type. Parentheses are optional.",
                 (answer_type(name, PYTHON + "stdtypes.html#" + owner + "." + name, [name + "()", owner + "." + name])
                  for name in dir(native) if not name.startswith("_") and callable(getattr(native, name))),
                 IDENTIFIERS, common=anchors, root=featured, sensitive=True)

    modules = [
        (path, name)
        for key in ("python-file-modules", "python-archive-modules")
        for path, name in re.findall(
            r'<li class="toctree-l1"><a[^>]+href="([^"]+)"[^>]*><code[^>]+><span[^>]*>([a-z_.]+)</span>',
            bank.text(key),
        )
    ]
    bank.add("python-file-modules", "Python", "Name a Python module for working with files or archives.",
             "Use a module in the File and Directory Access or Data Compression and Archiving chapter of the standard library.",
             (answer_type(name, urljoin(PYTHON, path)) for path, name in modules),
             IDENTIFIERS, common="pathlib|os.path|shutil|glob|tempfile|fileinput|zipfile|gzip", root="filecmp")

    java = """abstract continue for new switch assert default if package synchronized boolean do goto
        private this break double implements protected throw byte else import public throws
        case enum instanceof return transient catch extends int short try char final interface static void
        class finally long strictfp volatile const float native super while _"""
    go = bank.text("go-spec").split('id="Keywords"')[1]
    ecma = bank.text("ecma-lexical").split("<emu-production name=ReservedWord", 1)[1].split("</emu-production>", 1)[0]
    rust = bank.text("rust-keywords").split('id="r-lex.keywords.strict.syntax"', 1)[1].split('id="r-lex.keywords.strict.edition2018"', 1)[0]
    rust_words = re.findall(r"<span class=\"grammar-literal\">([^<]+)</span>", rust)
    if not rust_words:
        rust_words = re.findall(r"<code>([A-Za-z_]+)</code>", rust)
    php = bank.text("php-keywords").split('id="reserved.keywords"')[1].split("</table>", 1)[0]
    php_values = []
    for cell in re.findall(r"<td>(.*?)</td>", php, re.S):
        label = html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().removesuffix("()")
        if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", label):
            php_values.append(label)
    for slug, category, label, values, source, anchors, featured in [
        ("java-keywords", "Java", "Java", java.split(), "https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html#jls-3.9",
         "class|public|static|void|new|return|extends|if|private|int", "strictfp"),
        ("go-keywords", "Go", "Go", names_in_pre(go), "https://go.dev/ref/spec#Keywords",
         "func|package|import|var|return|for|if|go|type", "fallthrough"),
        ("js-keywords", "JavaScript", "JavaScript", ["let", *re.findall(r"<emu-t>([a-z]+)</emu-t>", ecma)],
         "https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html#sec-keywords-and-reserved-words",
         "const|let|var|return|function|class|if|else|switch", "debugger"),
        ("rust-keywords", "Rust", "Rust", rust_words, "https://doc.rust-lang.org/reference/keywords.html#strict-keywords",
         "fn|let|mut|pub|struct|impl|match|use|return", "extern"),
        ("php-keywords", "PHP", "PHP", php_values, "https://www.php.net/manual/en/reserved.keywords.php",
         "echo|function|class|return|if|else|foreach|include", "insteadof"),
    ]:
        qualifiers = {
            "Java": "Use a reserved keyword. Contextual keywords are separate.",
            "Go": "Use a reserved keyword from the Go language specification.",
            "JavaScript": "Use a reserved word from the ECMAScript lexical grammar, including let and yield.",
            "Rust": "Use a strict keyword from the Rust language reference.",
            "PHP": "Use a word from PHP’s keywords table.",
        }
        bank.plain(slug, category, f"Name a {label} keyword.", qualifiers[label], values,
                   source, IDENTIFIERS, common=anchors, root=featured, sensitive=label != "PHP")

    c = """auto break case char const continue default do double else enum extern float for goto if int long
        register return short signed sizeof static struct switch typedef union unsigned void volatile while
        inline restrict _Bool _Complex _Imaginary _Alignas _Alignof _Atomic _Generic _Noreturn _Static_assert _Thread_local"""
    bank.plain("c-keywords", "C", "Name a C keyword.",
               "Use a reserved language keyword from C17. Preprocessor directives and library names are separate.",
               c.split(), "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf", IDENTIFIERS,
               common="int|char|if|while|for|return|void|struct|sizeof|const|static", root="_Generic", sensitive=True)
    headers = """
        assert complex ctype errno fenv float inttypes iso646 limits locale math setjmp signal stdalign stdarg
        stdatomic stdbool stddef stdint stdio stdlib stdnoreturn string tgmath threads time uchar wchar wctype
    """.split()
    bank.add("c-headers", "C", "Name a C standard library header.",
             "Use a C17 standard header, with or without its angle brackets.",
             (answer_type(name + ".h", "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf",
                          ["<" + name + ".h>"]) for name in headers), IDENTIFIERS,
             common="stdio.h|stdlib.h|string.h|math.h|stdint.h|ctype.h|time.h|assert.h", root="tgmath.h", sensitive=True)


def command_line(bank, answer_type):
    git = bank.text("git-hooks-source")
    hooks = re.findall(r"^([a-z][a-z0-9-]+)\n~{4,}$", git, re.M)
    bank.plain("git-hooks", "Version control", "Name a Git hook.",
               "Use a hook in Git’s githooks manual.", hooks, "https://git-scm.com/docs/githooks",
               IDENTIFIERS, common="pre-commit|pre-push|commit-msg|post-merge|post-checkout|pre-receive",
               root="post-rewrite")

    bash = bank.text("bash-manual")
    for slug, headings, prompt, scope, anchors, featured in [
        ("shell-builtins", ("Bourne-Shell-Builtins-1", "Bash-Builtin-Commands", "Bash-History-Builtins-1"), "Name a Bash built-in command.",
         "Use a built-in listed by the Bash manual. Leave out options and arguments.",
         "cd|echo|pwd|export|read|printf|exit|alias|history|help", "getopts"),
        ("shell-variables", ("Bourne-Shell-Variables-1", "Bash-Variables-1"), "Name a shell variable.",
         "Use a variable listed in the Bash manual’s shell variables chapters.",
         "PATH|HOME|PWD|SHELL|PS1|HOSTNAME|LANG", "BASH_REMATCH"),
    ]:
        values = []
        for heading in headings:
            section = bash.split(f'id="{heading}"', 1)[1]
            section = re.split(r'<h[23] class=', section, maxsplit=1)[0]
            values.extend(html.unescape(name).strip().split()[0] for name in
                          re.findall(r'<dt>[^\n]*?<code class="code">([^<]+)', section))
        bank.plain(slug, "Command line", prompt, scope, values,
                   "https://www.gnu.org/software/bash/manual/bash.html#" + headings[-1],
                   IDENTIFIERS, common=anchors, root=featured)

    source = "https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/signal.h.html"
    signals = re.findall(r'<p class="tent">(SIG[A-Z0-9]+)</p>', bank.text("posix-signals"))
    bank.add("posix-signals", "Operating systems", "Name a Unix signal.",
             "Use a named signal from POSIX’s signal.h table. The SIG prefix is optional.",
             (answer_type(name, source, [name[3:]]) for name in signals),
             IDENTIFIERS, common="SIGINT|SIGTERM|SIGKILL|SIGSTOP|SIGSEGV|SIGABRT|SIGCHLD|SIGHUP", root="SIGPIPE")

    source = "https://github.com/torvalds/linux/blob/v6.12/arch/x86/entry/syscalls/syscall_64.tbl"
    calls = re.findall(r"^\d+\s+(?:common|64)\s+(\w+)(?:\s|$)", bank.text("linux-syscalls"), re.M)
    bank.add("linux-syscalls", "Operating systems", "Name a Linux system call.",
             "Use a syscall from the Linux x86-64 syscall table. Parentheses are optional.",
             (answer_type(name, source, [name + "()"]) for name in calls),
             IDENTIFIERS, common="read|write|open|close|fork|execve|exit|mmap|socket|bind", root="getdents64")

    distro_names = {
        "almalinux": "AlmaLinux", "alpinelinux": "Alpine Linux", "alt": "ALT regular", "altlinux": "ALT Linux", "archlinux": "Arch Linux",
        "centos": "CentOS", "debian": "Debian", "elementary": "elementary OS", "fedora": "Fedora",
        "gentoo": "Gentoo", "kali": "Kali Linux", "linuxmint": "Linux Mint", "mageia": "Mageia",
        "manjaro": "Manjaro", "opensuse": "openSUSE", "gnome": "GNOME OS", "nixos": "NixOS", "popos": "Pop!_OS", "rocky": "Rocky Linux",
        "rhel": "Red Hat Enterprise Linux", "sles": "SUSE Linux Enterprise Server",
        "ubuntu": "Ubuntu", "void": "Void Linux", "zorin": "Zorin OS",
    }
    distributions = {}
    with tarfile.open(bank.folder / "osinfo", mode="r:xz") as archive:
        for member in archive:
            if "/data/os/" not in member.name or not member.name.endswith(".xml.in") or not member.isfile():
                continue
            os = ElementTree.parse(archive.extractfile(member)).getroot().find("os")
            if os is not None and os.findtext("family") == "linux" and (distro := os.findtext("distro")):
                if distro not in distributions:
                    label = distro_names.get(distro, distro)
                    distributions[distro] = answer_type(label, "https://libosinfo.org/download.html", [distro])
    for name, url in {
        "Kali Linux": "https://www.kali.org/get-kali/",
        "Linux Mint": "https://linuxmint.com/",
        "Raspberry Pi OS": "https://www.raspberrypi.com/software/",
        "Zorin OS": "https://zorin.com/os/",
    }.items():
        variants = {"Kali Linux": ["Kali"], "Linux Mint": ["Mint"], "Raspberry Pi OS": ["Raspbian"]}
        distributions[name] = answer_type(name, url, variants.get(name, []))
    bank.add("linux-distributions", "Operating systems", "Name a Linux distribution.",
             "The libosinfo catalog includes distros such as Ubuntu, plus this quiz also accepts Kali, Linux Mint, Raspberry Pi OS, and Zorin OS.",
             distributions.values(), "libosinfo database; factual names",
             common="Ubuntu|Debian|Fedora|Arch Linux|Linux Mint|openSUSE|Kali Linux|CentOS",
             root="Gentoo")

    desktops = re.findall(r"<tr><td>([^<]+)</td><td>([^<]+)</td></tr>", bank.text("xdg-desktops"))
    desktop_aliases = {"KDE": ["KDE Plasma", "Plasma"], "DDE": ["Deepin"], "TDE": ["Trinity"]}
    bank.add("desktop-environments", "Operating systems", "Name a Linux desktop environment.",
             "Use a desktop or shell from the FreeDesktop desktop-environment registry.",
             (answer_type(name, "https://specifications.freedesktop.org/menu/latest/onlyshowin-registry.html",
                          [label, *desktop_aliases.get(name, [])]) for name, label in desktops if name != "Old"),
             IDENTIFIERS, common="GNOME|KDE|XFCE|Cinnamon|MATE|LXDE|LXQt", root="Pantheon")


def references(bank, answer_type):
    for slug, category, prompt, scope, key, column, path, anchors, featured in [
        ("dns-records", "DNS", "Name a DNS record type.", "Use a named record type in IANA’s DNS registry.",
         "dns-types", "TYPE", "dns-parameters", "A|AAAA|CNAME|MX|TXT|NS|PTR|SOA|SRV|CAA", "DNAME"),
        ("http-cache-directives", "HTTP", "Name a Cache-Control directive.",
         "Use a directive in IANA’s HTTP cache registry. Leave out any assigned value.",
         "http-cache", "Cache Directive", "http-cache-directives", "no-cache|no-store|max-age|public|private|must-revalidate", "immutable"),
        ("http-auth-schemes", "HTTP", "Name an HTTP authentication scheme.",
         "Use a scheme name listed in IANA’s HTTP authentication registry.",
         "http-auth", "Authentication Scheme Name", "http-authschemes", "Basic|Bearer|Digest|Negotiate|HOBA", "SCRAM-SHA-256"),
    ]:
        values = (answer_type(row[column], IANA + path, registered_expansion(row[column], row.get("Meaning", "")))
                  for row in bank.csv(key) if row[column] and row[column].casefold()
                  not in {"unassigned", "reserved", "private use", "reserved for future use", "*"})
        bank.add(slug, category, prompt, scope, values, IDENTIFIERS, common=anchors, root=featured)

    aliases = {
        "pypi": ["Python Package Index", "pip"], "npm": ["Node Package Manager"], "cargo": ["crates.io"],
        "gem": ["RubyGems"], "deb": ["Debian"], "apk": ["Alpine Package Keeper"], "alpm": ["pacman"],
        "brew": ["Homebrew"], "golang": ["Go modules", "Go"], "docker": ["Docker Hub"],
    }
    bank.add("package-ecosystems", "Package management", "Name a software package ecosystem.",
             "Use one of the specific ecosystems in the Package URL type index. Common ecosystem names count.",
             (answer_type(name, "https://github.com/package-url/purl-spec/blob/main/purl-types-index.json", aliases.get(name, []))
              for name in bank.json("purl") if name != "generic"),
             IDENTIFIERS, common="npm|pypi|cargo|maven|nuget|composer|gem|docker|brew", root="cpan")

    countries = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", bank.text("dns-root"), re.S):
        match = re.search(r'/domains/root/db/[^"\']+["\']>\s*(\.[^<\s]+)', row)
        if match and "domain-generic." in row:
            name = html.unescape(match[1])
            countries.append(answer_type(name, "https://www.iana.org/domains/root/db", list(domain_aliases(name))))
    bank.add("generic-domains", "DNS", "Name a generic top-level domain.",
             "Use a domain in IANA’s generic category. Country-code domains have a separate category.",
             countries, IDENTIFIERS, common=".com|.org|.net|.info|.xyz|.app|.dev", root=".museum")

    window_functions = re.findall(r"<dt><p><b>([a-z_]+)\(", bank.text("sql-window"))
    bank.add("sql-window-functions", "SQL", "Name a SQL window function.",
             "Use a function from SQLite’s built-in window-function list. Leave out the arguments.",
             (answer_type(name, "https://www.sqlite.org/windowfunctions.html#builtins", [name + "()"])
              for name in window_functions),
             IDENTIFIERS, common="row_number|rank|dense_rank|lag|lead", root="nth_value")

    term_aliases = nist_aliases(bank.text("nist-terms"))
    for slug, type_name, scope, anchors, featured in [
        ("graph-algorithms", "graph", "Use a named algorithm in the NIST graph algorithms index.",
         "breadth-first search|depth-first search|Dijkstra's algorithm|Kruskal's algorithm|Floyd-Warshall algorithm", "Boruvka's algorithm"),
        ("tree-structures", "tree", "Use a data structure in the NIST tree index.",
         "binary tree|binary search tree|AVL tree|trie|B-tree|red-black tree", "treap"),
        ("algorithmic-techniques", "T", "Use a technique in the NIST Algorithmic Techniques index.",
         "backtracking|brute force|divide and conquer|dynamic programming|greedy algorithm", "branch and bound"),
    ]:
        try:
            section = bank.text("nist-types" if type_name == "T" else "nist-areas").split(f'<h2><a name="{type_name}">')[1].split("</ul>", 1)[0]
        except IndexError as error:
            raise ValueError(f"Missing NIST index section {type_name}") from error
        rows = {}
        for link, label, kind in re.findall(
            r'<li><a href="(HTML/[^"]+)">(.*?)</a>(?: \[<strong>([A-Z])</strong>\])?</li>', section
        ):
            if type_name != "T" and kind != ("S" if type_name == "tree" else "A"):
                continue
            name = html.unescape(re.sub("<[^>]+>", "", label))
            variants = [name.replace("-", " ")]
            if slug != "tree-structures":
                variants.extend(term_aliases.get(link, []))
            if name == "breadth-first search":
                variants.append("BFS")
            if name == "depth-first search":
                variants.append("DFS")
            if link in rows and name in anchors.split("|"):
                earlier = rows[link]
                rows[link] = answer_type(name, NIST + link, [earlier.name, *earlier.aliases, *variants])
            elif link in rows:
                rows[link].aliases.extend([name, *variants])
            else:
                rows[link] = answer_type(name, NIST + link, variants)
        prompts = {
            "graph": "Name an algorithm for working with a graph.",
            "tree": "Name a tree data structure.",
            "T": "Name an algorithmic technique.",
        }
        bank.add(slug, "Data structures" if type_name == "tree" else "Algorithms",
                 prompts[type_name], scope, rows.values(), "NIST DADS; factual names",
                 common=anchors, root=featured)


def infrastructure(bank, answer_type):
    catalog = yaml.safe_load(bank.text("cncf"))["landscape"]
    projects = {}
    for group in catalog:
        for section in group.get("subcategories") or ():
            projects.setdefault(section["name"], section.get("items") or ())

    aliases = {
        "Amazon Elastic Container Registry (ECR)": ["AWS ECR", "ECR"],
        "Azure Registry": ["Azure Container Registry", "ACR"],
        "Podman Container Tools": ["Podman"],
        "Amazon Elastic Container Service (ECS)": ["Amazon ECS", "ECS"],
        "Kubernetes": ["K8s"],
        "Argo": ["Argo CD", "ArgoCD"],
        "Azure Pipelines": ["Azure DevOps Pipelines"],
        "Kafka": ["Apache Kafka"],
        "Pulsar": ["Apache Pulsar"],
        "Flink": ["Apache Flink"],
        "AWS Lambda": ["Lambda", "Amazon Lambda"],
        "Amazon CloudWatch": ["CloudWatch"],
        "Amazon Elastic Block Store (EBS)": ["Amazon EBS", "AWS EBS"],
        "Chef Infra": ["Chef"],
        "APISIX": ["Apache APISIX"],
    }
    extras = {
        "container-registries": {
            "Docker Hub": ("https://docs.docker.com/docker-hub/", ["docker.io"]),
            "GitHub Container Registry": ("https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry", ["ghcr.io", "GHCR"]),
            "Google Artifact Registry": ("https://cloud.google.com/artifact-registry/docs", ["Artifact Registry"]),
        },
        "container-runtimes": {"Docker Engine": ("https://docs.docker.com/engine/", ["Docker"])},
    }
    source = "https://landscape.cncf.io/"
    for slug, category, catalog_section, prompt, common, root in [
        ("infra-tools", "Infrastructure", "Automation & Configuration",
         "Name an infrastructure automation tool.", "Terraform|Ansible|Puppet|Chef Infra|Pulumi|OpenTofu|AWS CloudFormation", "CFEngine"),
        ("container-registries", "Containers", "Container Registry",
         "Name a container image registry.", "Docker Hub|GitHub Container Registry|Harbor|Amazon Elastic Container Registry (ECR)|Azure Registry|Quay|JFrog Artifactory", "zot"),
        ("container-runtimes", "Containers", "Container Runtime",
         "Name a container runtime.", "Docker Engine|containerd|runc|Podman Container Tools|CRI-O|lxd|gVisor", "Kata Containers"),
        ("container-orchestrators", "Containers", "Scheduling & Orchestration",
         "Name a container orchestration or scheduling tool.", "Kubernetes|Docker Swarm|Nomad|Apache Mesos|Amazon Elastic Container Service (ECS)", "Karmada"),
        ("messaging-platforms", "Distributed systems", "Streaming & Messaging",
         "Name a tool for event streaming or messaging.", "Kafka|RabbitMQ|NATS|Pulsar|Flink|Amazon Kinesis", "Pravega"),
        ("ci-tools", "Build and release", "Continuous Integration & Delivery",
         "Name a CI or CD tool.", "GitHub Actions|GitLab|Jenkins|CircleCI|Travis CI|Azure Pipelines|Buildkite|TeamCity|Argo", "GoCD"),
        ("monitoring-tools", "Observability", "Observability",
         "Name a tool for monitoring or observing an application.", "Prometheus|Grafana|Datadog|Amazon CloudWatch|Azure Monitor|Fluentd|Grafana Loki", "Graphite"),
        ("api-gateways", "Distributed systems", "API Gateway",
         "Name an API gateway.", "Kong|Traefik|ngrok|Azure API Management|APISIX|Tyk", "KrakenD"),
        ("cloud-storage-tools", "Infrastructure", "Cloud Native Storage",
         "Name a storage service or tool used by cloud applications.", "MinIO|Ceph|Amazon Elastic Block Store (EBS)|Azure Disk Storage|Google Persistent Disk|Gluster", "MooseFS"),
        ("serverless-platforms", "Infrastructure", "Hosted Platform",
         "Name a hosted serverless platform.", "AWS Lambda|Azure Functions|Cloudflare Workers|Google Cloud Run|Vercel|Netlify Functions", "IBM Cloud Code Engine"),
    ]:
        items = projects[catalog_section]
        rows = []
        for item in items:
            if not (name := item.get("name")):
                continue
            link = item.get("homepage_url") or item.get("repo_url") or source
            rows.append(answer_type(name, link if link.startswith("https://") else source, aliases.get(name, [])))
        additions = extras.get(slug, {})
        rows.extend(answer_type(name, link, variants) for name, (link, variants) in additions.items())
        scope = f"Use a tool listed under {catalog_section} in the CNCF Landscape."
        if additions:
            scope += " Also accepted: " + ", ".join(additions) + "."
        bank.add(slug, category, prompt, scope, rows, "CNCF Landscape and project documentation; factual names",
                 common=common, root=root)


def application_tools(bank, answer_type):
    source = "https://github.com/awesome-selfhosted/awesome-selfhosted"
    readme = bank.text("selfhosted")
    aliases = {
        "Apache HTTP Server": ["Apache", "httpd"], "code-server": ["VS Code in the browser", "Coder code-server"],
        "Mediawiki": ["Media Wiki"], "Dokuwiki": ["Doku Wiki"], "Joomla!": ["Joomla"],
        "Apache Solr": ["Solr"], "Ghost": ["Ghost CMS"], "OpenSearch": ["Open Search"],
    }
    for slug, category, heading, prompt, common, root in [
        ("web-servers", "Web hosting", "Web Servers", "Name a web server or reverse proxy.",
         "NGINX|Apache HTTP Server|Caddy|HAProxy|Traefik|Lighttpd", "Ferron"),
        ("browser-ides", "Development tools", "Software Development - IDE & Tools", "Name a browser-based development tool.",
         "code-server|JupyterLab|Eclipse Che|Coder|RStudio Server", "Atheos"),
        ("project-tools", "Development tools", "Software Development - Project Management",
         "Name a development project management or code collaboration tool.",
         "GitLab|Gitea|Gerrit|Redmine|Trac|OpenProject|Forgejo", "Review Board"),
        ("search-platforms", "Web applications", "Search Engines", "Name a self-hostable search engine.",
         "Elasticsearch|Apache Solr|OpenSearch|SearXNG|MeiliSearch|Typesense", "Yacy"),
        ("wiki-engines", "Web applications", "Wikis", "Name a wiki engine.",
         "Mediawiki|Dokuwiki|Wiki.js|XWiki|BookStack|TiddlyWiki", "PmWiki"),
        ("forum-software", "Web applications", "Communication - Social Networks and Forums",
         "Name software for running a forum or social network.",
         "Discourse|phpBB|Mastodon|Lemmy|Flarum|NodeBB|MyBB", "Friendica"),
        ("cms", "Web applications", "Content Management Systems (CMS)", "Name a content management system.",
         "WordPress|Drupal|Joomla!|Strapi|Payload CMS", "Plone"),
        ("analytics-tools", "Web applications", "Analytics", "Name a self-hostable web analytics tool.",
         "Matomo|Plausible Analytics|Umami|GoAccess|GoatCounter", "Offen"),
    ]:
        section = re.search(r"^### " + re.escape(heading) + r"\n(.*?)(?=^#{1,3} |\Z)", readme, re.M | re.S)[1]
        rows = []
        for name, link in re.findall(r"^- \[([^\]]+)\]\((https?://[^)]+)\)[^\n]* - ", section, re.M):
            rows.append(answer_type(name, link if link.startswith("https://") else source, aliases.get(name, [])))
        scope = f"Use a project in the {heading} section of Awesome Selfhosted."
        if slug == "search-platforms":
            rows.append(answer_type("Elasticsearch", "https://www.elastic.co/docs/products/elasticsearch"))
            scope += " Elasticsearch also counts."
        bank.add(slug, category, prompt, scope, rows, "Awesome Selfhosted catalog and project documentation; names",
                 common=common, root=root)

    archive_types = {
        "application/gzip", "application/zip", "application/x-zip-compressed", "application/x-tar",
        "application/vnd.rar", "application/x-rar-compressed", "application/x-7z-compressed",
        "application/x-bzip", "application/x-bzip2", "application/x-xz", "application/x-lzma",
        "application/x-lzip", "application/x-zstd", "application/zstd", "application/x-ace-compressed",
        "application/x-cpio", "application/x-compress", "application/x-gtar", "application/x-archive",
    }
    mime = bank.json("mime-db")
    rows = [
        answer_type("." + name, "https://github.com/jshttp/mime-db/blob/v1.54.0/db.json", [name])
        for kind in sorted(archive_types) for name in mime.get(kind, {}).get("extensions", ())
    ]
    bank.add("archive-extensions", "File formats", "Name an archive or compressed-file extension.",
             "Use an extension for an archive or compression media type in mime-db. The leading dot is optional.",
             rows, "MIT (mime-db metadata)", common=".zip|.tar|.gz|.rar|.7z|.bz2|.xz", root=".cpio")


def extra_catalogs(bank, answer_type):
    for category in (web, languages, command_line, references, infrastructure, application_tools):
        category(bank, answer_type)
