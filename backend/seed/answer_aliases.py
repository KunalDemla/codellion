"""Alternate names and spellings scoped to the questions where they apply."""

import re


TREE_ALIASES = {
    "binary tree": ("BT",),
    "binary search tree": ("BST",),
    "AVL tree": ("AVL", "Adelson-Velsky and Landis tree"),
    "red-black tree": ("RB tree", "RBT"),
    "B+-tree": ("B plus tree", "B+ tree"),
    "B*-tree": ("B star tree", "B* tree"),
    "hash tree": ("Merkle tree",),
    "Patricia tree": ("PATRICIA trie",),
    "treap": ("tree heap",),
}

TRAVERSAL_ALIASES = {
    "breadth-first search": ("BFS", "breadth-first traversal"),
    "depth-first search": ("DFS", "depth-first traversal"),
}

ALIASES = {
    "programming-languages": {
        "JavaScript": ("ECMAScript",),
        "C++": ("C plus plus",),
        "C#": ("C sharp",),
        "F#": ("F sharp",),
        "Objective-C": ("Obj C", "Objective C"),
        "Objective-C++": ("Obj C++", "Objective C++"),
    },
    "markup-languages": {
        "HTML": ("HyperText Markup Language",),
        "XML": ("Extensible Markup Language",),
        "CSS": ("Cascading Style Sheets",),
        "Rich Text Format": ("RTF",),
        "reStructuredText": ("reST", "rst"),
    },
    "data-formats": {
        "JSON": ("JavaScript Object Notation",),
        "JSON with Comments": ("JSONC",),
        "JSONLD": ("JSON-LD", "JSON for Linked Data"),
        "YAML": ("YAML Ain't Markup Language", "YAML Ain’t Markup Language"),
        "CSV": ("comma-separated values", "comma separated values"),
        "TSV": ("tab-separated values", "tab separated values"),
        "TOML": ("Tom's Obvious Minimal Language", "Tom’s Obvious Minimal Language"),
        "XML": ("Extensible Markup Language",),
        "edn": ("Extensible Data Notation",),
        "XML Property List": ("XML plist",),
    },
    "database-engines": {
        "PostgreSQL": ("Postgres", "PGSQL"),
        "Microsoft SQL Server": ("MS SQL Server", "MS SQL", "MSSQL", "SQL Server"),
        "Microsoft Access": ("MS Access",),
        "IBM Db2": ("Db2", "DB 2"),
        "Oracle": ("Oracle Database", "Oracle DB"),
        "Amazon DynamoDB": ("DynamoDB", "AWS DynamoDB"),
        "Amazon Redshift": ("Redshift", "AWS Redshift"),
        "Google BigQuery": ("BigQuery", "GCP BigQuery"),
        "Microsoft Azure SQL Database": ("Azure SQL Database",),
        "Microsoft Azure Cosmos DB": ("Azure Cosmos DB", "Cosmos DB"),
        "Apache Spark (SQL)": ("Spark SQL", "Apache Spark SQL"),
    },
    "sql-aggregates": {
        "avg": ("average",),
    },
    "software-licenses": {
        "BSL-1.0": ("BSL", "Boost License", "Boost Software License", "BSL 1.0"),
        "Apache-2.0": ("Apache 2", "Apache 2.0", "Apache License 2", "Apache License Version 2.0"),
        "BSD-2-Clause": ("Simplified BSD", "FreeBSD License"),
        "BSD-3-Clause": ("New BSD", "Modified BSD", "Revised BSD"),
        "0BSD": ("Zero-Clause BSD", "BSD 0-Clause"),
        "ISC": ("Internet Systems Consortium License",),
        "BlueOak-1.0.0": ("Blue Oak Model License", "Blue Oak License"),
        "MS-PL": ("Microsoft Public License", "MsPL"),
        "MS-RL": ("Microsoft Reciprocal License", "MsRL"),
        "PostgreSQL": ("Postgres License",),
    },
    "target-platforms": {
        "darwin": ("Mac", "Macintosh"),
        "dragonfly": ("DragonFly BSD", "DragonFlyBSD"),
        "illumos": ("illumos OS",),
    },
    "cpu-architectures": {
        "amd64": ("AMD 64", "Intel 64", "EM64T"),
        "x86": ("x86-32", "IA-32", "IA32", "i686"),
        "arm": ("ARM32", "AArch32", "32-bit ARM"),
        "arm64": ("ARMv8-A (AArch64)", "64-bit ARM"),
        "wasm": ("Web Assembly",),
        "loong64": ("LoongArch64", "LA64"),
        "mips64le": ("MIPS64 little-endian",),
        "mipsle": ("MIPS little-endian",),
        "ppc64": ("PPC 64",),
        "ppc64le": ("PowerPC64LE", "PowerPC 64 LE"),
        "sparc64": ("64-bit SPARC",),
        "s390x": ("z/Architecture",),
    },
    "http-status-names": {
        "Internal Server Error": ("ISE",),
        "URI Too Long": ("Request-URI Too Long", "Request URI Too Long", "URL Too Long"),
        "Range Not Satisfiable": ("Requested Range Not Satisfiable",),
        "Not Extended (OBSOLETED)": ("Not Extended",),
        "I'm a teapot": ("Im a teapot", "I am a teapot"),
    },
    "http-auth-schemes": {
        "Basic": ("Basic Auth", "HTTP Basic Authentication"),
        "Digest": ("Digest Auth", "HTTP Digest Authentication"),
        "Bearer": ("Bearer Auth", "Bearer Token"),
        "DPoP": ("Demonstrating Proof of Possession",),
    },
    "network-services": {
        "http": ("Hypertext Transfer Protocol",),
        "https": ("Hypertext Transfer Protocol Secure",),
        "ssh": ("Secure Shell",),
        "ftp": ("File Transfer Protocol",),
        "tftp": ("Trivial File Transfer Protocol",),
        "domain": ("Domain Name System",),
        "smtp": ("Simple Mail Transfer Protocol",),
        "imap": ("Internet Message Access Protocol",),
        "pop3": ("POP", "Post Office Protocol", "Post Office Protocol 3"),
        "ntp": ("Network Time Protocol",),
        "snmp": ("Simple Network Management Protocol",),
        "bootps": ("DHCP Server", "Dynamic Host Configuration Protocol"),
        "bootpc": ("DHCP Client",),
        "ldap": ("Lightweight Directory Access Protocol",),
        "microsoft-ds": ("SMB", "Server Message Block"),
        "ms-wbt-server": ("RDP", "Remote Desktop Protocol"),
        "rfb": ("Remote Framebuffer",),
    },
    "uri-schemes": {
        "http": ("Hypertext Transfer Protocol",),
        "https": ("Hypertext Transfer Protocol Secure",),
        "ftp": ("File Transfer Protocol",),
        "ws": ("WebSocket",),
        "wss": ("Secure WebSocket", "WebSocket Secure"),
    },
    "character-encodings": {
        "US-ASCII": ("ASCII",),
        "UTF-8": ("Unicode Transformation Format 8",),
        "Shift_JIS": ("SJIS", "Shift JIS"),
    },
    "data-structures": {
        **TREE_ALIASES,
        "doubly linked list": ("DLL",),
        "priority queue": ("PQ",),
        "deque": ("double-ended queue", "double ended queue"),
        "k-d tree": ("KD tree", "k-dimensional tree"),
    },
    "tree-structures": TREE_ALIASES,
    "sorting-algorithms": {
        "bidirectional bubble sort": ("cocktail sort", "cocktail shaker sort", "shaker sort"),
        "introsort": ("introspective sort",),
    },
    "graph-algorithms": {
        **TRAVERSAL_ALIASES,
        "Dijkstra's algorithm": ("Dijkstra", "Dijkstras algorithm"),
        "Kruskal's algorithm": ("Kruskal", "Kruskals algorithm"),
        "Floyd-Warshall algorithm": ("Floyd-Warshall", "Floyd Warshall"),
        "Bellman-Ford algorithm": ("Bellman-Ford", "Bellman Ford"),
        "Prim-Jarnik algorithm": ("Prim", "Prim's algorithm", "Jarnik's algorithm"),
        "Ford-Fulkerson method": ("Ford-Fulkerson", "Ford Fulkerson"),
        "Boruvka's algorithm": ("Boruvka", "Borůvka", "Borůvka's algorithm"),
    },
    "search-algorithms": {
        **TRAVERSAL_ALIASES,
        "KMP": ("Knuth–Morris–Pratt", "Knuth-Morris-Pratt", "Knuth Morris Pratt"),
    },
    "algorithmic-techniques": {
        "dynamic programming": ("DP",),
        "polynomial approximation scheme": ("PTAS", "polynomial-time approximation scheme"),
        "fully polynomial approximation scheme": ("FPTAS", "fully polynomial-time approximation scheme"),
    },
    "dns-records": {
        "A": ("IPv4 address record", "IPv4 address"),
        "AAAA": ("IPv6 address record", "IPv6 address", "quad A"),
        "CNAME": ("canonical name", "canonical name record"),
        "MX": ("mail exchange", "mail exchanger", "mail exchange record"),
        "TXT": ("text record",),
        "NS": ("name server", "nameserver", "name server record"),
        "PTR": ("pointer record", "reverse DNS pointer"),
        "SOA": ("start of authority",),
        "SRV": ("service record", "service locator"),
        "CAA": ("certification authority authorization",),
        "DS": ("delegation signer",),
        "NAPTR": ("naming authority pointer",),
        "RRSIG": ("resource record signature",),
        "SVCB": ("service binding",),
    },
    "posix-signals": {
        "SIGSEGV": ("segmentation fault", "segfault", "segmentation violation"),
        "SIGTERM": ("termination signal",),
        "SIGWINCH": ("window size change",),
    },
    "linux-distributions": {
        "Red Hat Enterprise Linux": ("RHEL",),
        "SUSE Linux Enterprise Server": ("SLES",),
        "Alpine Linux": ("Alpine",),
        "Raspberry Pi OS": ("Raspbian",),
    },
    "desktop-environments": {
        "LXDE": ("Lightweight X11 Desktop Environment",),
        "Razor": ("Razor-qt", "RazorQt"),
        "EDE": ("Equinox Desktop Environment",),
    },
    "infra-tools": {
        "AWS CloudFormation": ("CloudFormation", "Amazon CloudFormation"),
        "Chef Infra": ("Chef",),
        "Salt Project": ("Salt", "SaltStack"),
        "VMware vSphere": ("vSphere",),
    },
    "container-registries": {
        "GitHub Container Registry": ("GHCR", "ghcr.io"),
        "Google Container Registry": ("GCR", "gcr.io", "Google Cloud Container Registry"),
        "Google Artifact Registry": ("GAR", "Google Cloud Artifact Registry"),
        "Docker Hub": ("hub.docker.com",),
        "Quay": ("Quay.io", "Red Hat Quay"),
    },
    "container-runtimes": {
        "Docker Engine": ("Docker",),
        "Singularity": ("SingularityCE", "Singularity CE"),
        "Firecracker": ("AWS Firecracker",),
    },
    "container-orchestrators": {
        "Kubernetes": ("Kube",),
        "Nomad": ("HashiCorp Nomad",),
        "Apache Mesos": ("Mesos",),
    },
    "messaging-platforms": {
        "Amazon Kinesis": ("Kinesis", "AWS Kinesis"),
        "Apache RocketMQ": ("RocketMQ",),
        "Apache NiFi": ("NiFi",),
        "Apache Spark": ("Spark",),
        "Apache Storm": ("Storm",),
        "Azure Event Hubs": ("Event Hubs",),
    },
    "ci-tools": {
        "GitHub Actions": ("GHA",),
        "GitLab": ("GitLab CI", "GitLab CD", "GitLab CI/CD"),
        "AWS CodePipeline": ("CodePipeline", "Amazon CodePipeline"),
        "Google Cloud Build": ("Cloud Build", "GCP Cloud Build"),
        "TeamCity": ("JetBrains TeamCity",),
        "Bamboo": ("Atlassian Bamboo",),
        "Flux": ("Flux CD", "FluxCD"),
        "Cloudbees Codeship": ("Codeship",),
        "JenkinsX": ("Jenkins X", "jx"),
        "Woodpecker CI": ("Woodpecker",),
        "Harness.io": ("Harness",),
    },
    "monitoring-tools": {
        "Amazon CloudWatch": ("CloudWatch", "AWS CloudWatch"),
        "Grafana Loki": ("Loki",),
        "Azure Monitor": ("Microsoft Azure Monitor",),
    },
    "api-gateways": {
        "Kong": ("Kong Gateway", "Kong API Gateway"),
        "Azure API Management": ("APIM", "Azure APIM"),
        "MuleSoft": ("MuleSoft Anypoint API Gateway", "Anypoint API Gateway"),
        "APISIX": ("Apache APISIX",),
        "3Scale": ("Red Hat 3scale",),
    },
    "cloud-storage-tools": {
        "Amazon Elastic Block Store (EBS)": ("AWS EBS", "Amazon EBS", "Elastic Block Store"),
        "Gluster": ("GlusterFS",),
        "Google Persistent Disk": ("Google Cloud Persistent Disk",),
        "Swift": ("OpenStack Swift",),
    },
    "serverless-platforms": {
        "AWS Lambda": ("Lambda", "Amazon Lambda"),
        "Google Cloud Run": ("Cloud Run", "GCP Cloud Run"),
    },
    "web-servers": {
        "NGINX": ("engine x",),
        "Apache HTTP Server": ("Apache", "Apache httpd", "httpd"),
        "Lighttpd": ("lighty",),
        "Nginx Proxy Manager": ("NPM",),
        "Caddy": ("Caddy Server", "Caddy Web Server"),
    },
    "browser-ides": {
        "code-server": ("Coder code-server",),
    },
    "project-tools": {
        "Gerrit": ("Gerrit Code Review",),
        "Fossil": ("Fossil SCM",),
        "Sourcehut": ("sr.ht",),
    },
    "search-platforms": {
        "Apache Solr": ("Solr",),
        "Manticore Search": ("Manticore",),
    },
    "wiki-engines": {
        "docmost Community Edition": ("Docmost", "Docmost CE"),
        "Zim": ("Zim Desktop Wiki",),
    },
    "forum-software": {
        "Simple Machines Forum": ("SMF", "Simple Machines"),
        "OSSN": ("Open Source Social Network",),
        "diaspora*": ("diaspora",),
    },
    "cms": {
        "WordPress": ("WP", "WordPress.org"),
        "Payload CMS": ("Payload",),
        "Backdrop CMS": ("Backdrop",),
        "Bolt CMS": ("Bolt",),
        "Alfresco Community Edition": ("Alfresco", "Alfresco CE"),
        "Concrete 5 CMS": ("concrete5", "Concrete CMS"),
        "KeystoneJS": ("Keystone",),
    },
    "analytics-tools": {
        "Matomo": ("Piwik",),
        "Plausible Analytics": ("Plausible",),
        "Countly Community Edition": ("Countly", "Countly CE"),
        "Superset": ("Apache Superset",),
    },
}

NAMED_CATALOGS = {
    "programming-languages", "markup-languages", "data-formats", "database-engines",
    "data-structures", "sorting-algorithms", "search-algorithms", "web-browsers",
    "linux-distributions", "desktop-environments", "graph-algorithms",
    "tree-structures", "algorithmic-techniques", "infra-tools",
    "container-registries", "container-runtimes", "container-orchestrators",
    "messaging-platforms", "ci-tools", "monitoring-tools", "api-gateways",
    "cloud-storage-tools", "serverless-platforms", "web-servers", "browser-ides",
    "project-tools", "search-platforms", "wiki-engines", "forum-software",
    "cms", "analytics-tools",
}
SEPARATED_NAMES = {
    "html-input-types", "html-attributes", "css-properties", "css-pseudo-classes",
    "css-pseudo-elements", "css-functions", "aria-roles", "sql-data-types",
    "git-hooks", "character-encodings", "http-status-names", "http-methods",
    "http-headers", "http-cache-directives", "http-auth-schemes",
}
CAMEL_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def formatting_aliases(slug, name):
    if slug == "python-exceptions":
        yield name.casefold()
        yield name.upper()
        spaced = CAMEL_CASE_BOUNDARY.sub(" ", name)
        yield spaced
        yield spaced.casefold()
        yield spaced.capitalize()
        yield spaced.upper()
        yield "builtins." + name
        yield "builtins." + name.casefold()
        return

    if slug == "http-headers":
        yield name + ":"
    elif slug == "python-types":
        yield "builtins." + name
    elif slug == "html-input-types":
        yield f'type="{name}"'
        yield f"type='{name}'"
    elif slug == "html-attributes" and name == "data_attributes":
        yield "data-*"

    if slug == "software-licenses":
        # Keep the full version and any exception or later-version qualifier.
        if "-" in name:
            yield name.replace("-", " ")
        return

    if slug not in NAMED_CATALOGS and slug not in SEPARATED_NAMES:
        return

    if "'" in name:
        yield name.replace("'", "’")
    if "-" in name:
        yield name.replace("-", "‐")
        yield name.replace("-", "‑")

    # Leave punctuation such as '+', '#', and '.' intact on technical names.
    if re.fullmatch(r"[^\W_]+(?:[ _-][^\W_]+)*", name):
        spaced = re.sub(r"[ _-]", " ", name)
        if slug in NAMED_CATALOGS or slug == "http-auth-schemes":
            spaced = CAMEL_CASE_BOUNDARY.sub(" ", spaced)
        if " " in spaced:
            yield spaced
            yield spaced.replace(" ", "")

    if slug in NAMED_CATALOGS:
        acronym = re.fullmatch(r"(.+) \(([A-Z][A-Z0-9-]{1,10})\)", name)
        if acronym:
            initials = "".join(word[0].upper() for word in acronym[1].split())
            if initials.endswith(acronym[2]):
                yield acronym[1]
                yield acronym[2]


def additional_aliases(slug, rows, normalize):
    explicit = {normalize(name): aliases for name, aliases in ALIASES.get(slug, {}).items()}
    return {
        normalize(row.name): [
            *explicit.get(normalize(row.name), ()), *formatting_aliases(slug, row.name),
        ]
        for row in rows
    }
