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
        "JSON": ("JavaScript Object Notation", ".json"),
        "JSON with Comments": ("JSONC",),
        "JSONLD": ("JSON-LD", "JSON for Linked Data"),
        "YAML": ("YAML Ain't Markup Language", "YAML Ain’t Markup Language", ".yaml", ".yml"),
        "CSV": ("comma-separated values", "comma separated values", ".csv"),
        "TSV": ("tab-separated values", "tab separated values", ".tsv"),
        "TOML": ("Tom's Obvious Minimal Language", "Tom’s Obvious Minimal Language", ".toml"),
        "XML": ("Extensible Markup Language",),
        "INI": ("initialization file", "Windows INI", ".ini"),
        "ABNF": ("Augmented Backus-Naur Form", "Augmented Backus Naur Form"),
        "ASN.1": ("ASN 1", "ASN1", "Abstract Syntax Notation One"),
        "ApacheConf": ("Apache configuration", "httpd.conf"),
        "Avro IDL": ("Avro Interface Definition Language", "AVDL", ".avdl"),
        "CODEOWNERS": ("CODEOWNERS file",),
        "COLLADA": ("Collaborative Design Activity", ".dae"),
        "CSON": ("CoffeeScript Object Notation", ".cson"),
        "Cabal Config": ("cabal.project", "cabal.config"),
        "Cloud Firestore Security Rules": ("Firestore Rules", "firestore.rules"),
        "CoNLL-U": ("CoNLL Unified", ".conllu"),
        "Cue Sheet": ("CUE sheet", ".cue"),
        "Debian Package Control File": ("Debian control file", "Debian package control"),
        "Diff": ("unified diff", ".diff"),
        "Dotenv": (".env", "env file"),
        "EBNF": ("Extended Backus-Naur Form", "Extended Backus Naur Form"),
        "EditorConfig": (".editorconfig",),
        "FIGlet Font": ("FIGlet font file", ".flf"),
        "GEDCOM": ("Genealogical Data Communication", ".ged"),
        "Git Attributes": (".gitattributes",),
        "Git Config": (".gitconfig", ".gitmodules"),
        "Git Revision List": (".git-blame-ignore-revs",),
        "Glyph Bitmap Distribution Format": ("BDF", ".bdf"),
        "Godot Resource": ("Godot text resource", ".tres"),
        "Graph Modeling Language": ("GML",),
        "Graphviz (DOT)": ("Graphviz", "DOT", "DOT language", ".dot"),
        "HOCON": ("Human-Optimized Config Object Notation", "Human Optimized Config Object Notation"),
        "HTTP": ("Hypertext Transfer Protocol",),
        "IFC": ("Industry Foundation Classes", ".ifc"),
        "Ignore List": (".gitignore",),
        "JAR Manifest": ("MANIFEST.MF",),
        "Java Properties": ("Java properties file", ".properties"),
        "Jest Snapshot": ("Jest snapshot file",),
        "KDL": ("KDL Document Language", ".kdl"),
        "KiCad Layout": ("KiCad PCB", ".kicad_pcb"),
        "KiCad Schematic": (".kicad_sch",),
        "LTspice Symbol": (".asy",),
        "M3U": ("M3U8", ".m3u", ".m3u8"),
        "Maven POM": ("pom.xml", "Maven Project Object Model"),
        "Microsoft Developer Studio Project": ("Developer Studio Project", ".dsp"),
        "Microsoft Visual Studio Solution": ("Visual Studio solution", ".sln"),
        "NEON": ("Nette Object Notation", ".neon"),
        "NPM Config": (".npmrc",),
        "Nginx": ("nginx.conf",),
        "OASv2-json": ("OpenAPI 2 JSON", "Swagger 2.0 JSON", "OAS v2 JSON"),
        "OASv2-yaml": ("OpenAPI 2 YAML", "Swagger 2.0 YAML", "OAS v2 YAML"),
        "OASv3-json": ("OpenAPI 3 JSON", "OAS v3 JSON"),
        "OASv3-yaml": ("OpenAPI 3 YAML", "OAS v3 YAML"),
        "Object Data Instance Notation": ("ODIN",),
        "OpenAPI Specification v2": ("OpenAPI 2", "OpenAPI 2.0", "OAS v2", "Swagger 2", "Swagger 2.0"),
        "OpenAPI Specification v3": ("OpenAPI 3", "OpenAPI v3", "OAS v3"),
        "OpenStep Property List": ("OpenStep plist", "ASCII property list", "ASCII plist"),
        "OpenType Feature File": ("OpenType features", ".fea"),
        "Pickle": ("Python Pickle", "Pickle protocol"),
        "Pip Requirements": ("requirements.txt", "pip requirements file"),
        "PlantUML": (".puml",),
        "Protocol Buffer Text Format": ("textproto", "protobuf text", ".textproto"),
        "RBS": ("Ruby Signature", ".rbs"),
        "RON": ("Rusty Object Notation", ".ron"),
        "ROS Interface": ("ROS interface definition",),
        "Readline Config": (".inputrc",),
        "Robots Exclusion Rules": ("robots.txt", "Robots Exclusion Protocol"),
        "SPARQL": ("SPARQL Protocol and RDF Query Language", ".sparql"),
        "SQL": ("Structured Query Language", ".sql"),
        "STAR": ("Self-defining Text Archive and Retrieval", "STAR file"),
        "STEP": ("ISO 10303-21", "STEP Part 21", ".stp", ".step"),
        "STL": ("STL ASCII", "ASCII stereolithography"),
        "STON": ("Smalltalk Object Notation", ".ston"),
        "ShellCheck Config": (".shellcheckrc",),
        "SubRip Text": ("SubRip", "SRT", ".srt"),
        "Tor Config": ("Tor configuration",),
        "Tree-sitter Query": ("Tree-sitter queries",),
        "Turtle": ("Terse RDF Triple Language", "RDF Turtle", ".ttl"),
        "Wavefront Material": ("MTL", ".mtl", "Wavefront MTL"),
        "Wavefront Object": (".obj", "Wavefront OBJ"),
        "Web Ontology Language": ("OWL", ".owl"),
        "WebVTT": ("Web Video Text Tracks", ".vtt"),
        "Windows Registry Entries": ("Windows Registry file", ".reg"),
        "XCompose": (".XCompose",),
        "YANG": ("Yet Another Next Generation", "YANG data model", ".yang"),
        "cURL Config": (".curlrc",),
        "desktop": ("desktop entry", "desktop entry file", ".desktop"),
        "dircolors": (".dircolors",),
        "edn": ("Extensible Data Notation",),
        "iCalendar": ("iCal format", "ICS", ".ics"),
        "nanorc": (".nanorc",),
        "vCard": ("VCF", ".vcf"),
        "XML Property List": ("XML plist",),
        "SVG": ("Scalable Vector Graphics", ".svg"),
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
        "MIT": ("Expat", "Expat License"),
        "MIT-0": ("MIT-0 License", "MIT No Attribution License", "No-attribution Expat License"),
        "BSL-1.0": ("BSL", "Boost License", "Boost Software License", "BSL 1.0"),
        "Apache-2.0": ("Apache 2", "Apache 2.0", "Apache v2", "Apache License 2", "Apache License v2",
                       "Apache License Version 2.0", "ALv2"),
        "BSD-1-Clause": ("1-clause BSD", "1 clause BSD"),
        "BSD-2-Clause": ("Simplified BSD", "FreeBSD License", "2-clause BSD", "2 clause BSD", "BSD2"),
        "BSD-3-Clause": ("New BSD", "Modified BSD", "Revised BSD", "3-clause BSD", "3 clause BSD", "BSD3"),
        "0BSD": ("Zero-Clause BSD", "Zero Clause BSD", "BSD 0-Clause", "0-clause BSD"),
        "ISC": ("Internet Systems Consortium License",),
        "BlueOak-1.0.0": ("Blue Oak Model License", "Blue Oak License", "Blue Oak 1.0.0"),
        "CERN-OHL-P-2.0": ("CERN OHL v2 Permissive", "CERN-OHL-P v2"),
        "CERN-OHL-S-2.0": ("CERN OHL v2 Strongly Reciprocal", "CERN-OHL-S v2"),
        "CERN-OHL-W-2.0": ("CERN OHL v2 Weakly Reciprocal", "CERN-OHL-W v2"),
        "CECILL-2.1": ("CeCILL License 2.1",),
        "HPND": ("Historical Permission Notice and Disclaimer License",),
        "MS-PL": ("Microsoft Public License", "MsPL"),
        "MS-RL": ("Microsoft Reciprocal License", "MsRL"),
        "NASA-1.3": ("NASA Open Source Agreement Version 1.3", "NOSA 1.3"),
        "NCSA": ("NCSA Open Source License", "University of Illinois Open Source License"),
        "OFL-1.1": ("SIL OFL 1.1", "Open Font License 1.1"),
        "PostgreSQL": ("Postgres License",),
        "Zlib": ("zlib/libpng license", "zlib/libpng"),
    },
    "target-platforms": {
        "darwin": ("Mac", "Macintosh"),
        "dragonfly": ("DragonFly BSD", "DragonFlyBSD"),
        "illumos": ("illumos OS",),
    },
    "cpu-architectures": {
        "amd64": ("AMD 64", "Intel 64", "EM64T", "x86 64", "64-bit x86"),
        "x86": ("x86-32", "IA-32", "IA32", "i486", "i586", "i686"),
        "arm": ("ARM32", "AArch32", "32-bit ARM"),
        "arm64": ("ARMv8-A (AArch64)", "64-bit ARM", "ARM 64", "AArch 64"),
        "wasm": ("Web Assembly", "wasm32", "WebAssembly 32-bit"),
        "riscv64": ("RV64", "64-bit RISC-V"),
        "loong64": ("LoongArch64", "LA64", "LoongArch 64", "64-bit LoongArch"),
        "mips": ("MIPS32", "32-bit MIPS", "MIPS32 big-endian"),
        "mips64": ("64-bit MIPS", "MIPS64 big-endian"),
        "mips64le": ("MIPS64 little-endian",),
        "mipsle": ("MIPS little-endian", "MIPS32LE", "MIPS32 little-endian"),
        "ppc64": ("PPC 64", "PowerPC 64-bit", "PowerPC64 big-endian"),
        "ppc64le": ("PowerPC64LE", "PowerPC 64 LE", "PowerPC64 little-endian", "PPC64EL"),
        "sparc64": ("64-bit SPARC", "SPARC V9", "SPARCV9"),
        "s390x": ("z/Architecture", "IBM System z", "64-bit System z"),
    },
    "python-exceptions": {
        "ZeroDivisionError": ("division by zero", "divide by zero", "divide by zero error"),
        "EOFError": ("end of file error", "end-of-file error", "End of File Error"),
        "IOError": ("I/O error", "I/O Error", "i/o error"),
        "OSError": ("operating system error", "Operating System Error", "WindowsError", "windowserror", "WINDOWSERROR"),
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
    "tree-structures": {
        **TREE_ALIASES,
        "AVL tree": ("AVL", "Adelson-Velsky and Landis tree", "Adelson-Velskii and Landis tree", "AVL search tree"),
        "trie": ("prefix tree", "prefix trie", "retrieval tree"),
        "(a,b)-tree": ("(a, b)-tree", "(a, b) tree", "a-b tree"),
        "balanced binary search tree": ("balanced BST",),
        "BB(α) tree": ("BB(alpha) tree", "BB alpha tree", "BB(α)-tree"),
        "BDD": ("binary decision diagram",),
        "binary tree representation of trees": ("left-child right-sibling tree", "left child right sibling tree",
                                                "left child-right sibling binary tree", "LCRS", "LCRS binary tree"),
        "Bk tree": ("BK-tree", "Burkhard-Keller tree", "Burkhard Keller tree"),
        "B+-tree": ("B plus tree", "B+ tree", "B+tree"),
        "B*-tree": ("B star tree", "B* tree", "B*tree"),
        "compact DAWG": ("CDAWG", "compact directed acyclic word graph"),
        "compact trie": ("compacted trie",),
        "double-ended priority queue": ("DEPQ", "double ended PQ", "double-ended PQ"),
        "Fibonacci heap": ("fib heap",),
        "height-balanced binary search tree": ("height-balanced BST", "height balanced BST"),
        "k-ary heap": ("k-way heap", "k way heap"),
        "k²-tree": ("k^2-tree", "k^2 tree", "k squared tree"),
        "leftist tree": ("leftist heap",),
        "multiway tree": ("multi-way tree", "multi way tree"),
        "Patricia tree": ("PATRICIA trie", "Practical Algorithm to Retrieve Information Coded in Alphanumeric"),
        "reduced ordered binary decision diagram": ("reduced ordered BDD", "reduced ordered binary decision diagram (ROBDD)"),
        "right-threaded tree": ("right threaded binary tree",),
        "R*-tree": ("R star tree", "R*tree"),
        "UB-tree": ("UB Tree",),
        "van Emde-Boas priority queue": ("van Emde Boas tree", "van Emde-Boas tree", "vEB", "vEB tree", "vEB priority queue"),
    },
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
        "Jenkins": ("Jenkins CI",),
        "Travis CI": ("Travis", "Travis-CI"),
        "Azure Pipelines": ("Microsoft Azure Pipelines",),
        "Buildkite": ("Buildkite Pipelines",),
        "Argo": ("Argo Project", "ArgoProj"),
        "Appveyor": ("AppVeyor CI",),
        "AWS CodePipeline": ("CodePipeline", "Amazon CodePipeline"),
        "Google Cloud Build": ("Cloud Build", "GCP Cloud Build"),
        "TeamCity": ("JetBrains TeamCity",),
        "Bamboo": ("Atlassian Bamboo",),
        "Concourse": ("Concourse CI", "Concourse-CI"),
        "Flux": ("Flux CD", "FluxCD"),
        "Cloudbees Codeship": ("Codeship",),
        "JenkinsX": ("Jenkins X", "jx"),
        "k6": ("Grafana k6",),
        "MockServer": ("Mock-Server",),
        "Octopus Deploy": ("Octopus",),
        "Screwdriver": ("Screwdriver CD", "Screwdriver.cd"),
        "Semaphore": ("Semaphore CI", "SemaphoreCI"),
        "Tekton": ("Tekton Pipelines", "Tekton CD", "TektonCD"),
        "Woodpecker CI": ("Woodpecker", "Woodpecker-CI"),
        "XL Deploy": ("XebiaLabs XL Deploy", "Digital.ai Deploy"),
        "Omnistrate (member)": ("Omnistrate",),
        "Zuul": ("Zuul CI",),
        "GoCD": ("Go-CD", "Thoughtworks GoCD"),
        "Harness.io": ("Harness", "Harness CI", "Harness CD"),
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
        "WordPress": ("WP", "WordPress.org", "WordPress CMS"),
        "Drupal": ("Drupal CMS",),
        "Joomla!": ("Joomla CMS",),
        "Strapi": ("Strapi CMS",),
        "Payload CMS": ("Payload",),
        "Apostrophe": ("ApostropheCMS", "Apostrophe CMS"),
        "Backdrop CMS": ("Backdrop",),
        "Bolt CMS": ("Bolt",),
        "Alfresco Community Edition": ("Alfresco", "Alfresco CE"),
        "CMS Made Simple": ("CMSMS", "CMS Made Simple CMS"),
        "Cockpit": ("Cockpit CMS", "GetCockpit"),
        "Concrete 5 CMS": ("concrete5", "Concrete CMS"),
        "eLabFTW": ("eLab FTW",),
        "KeystoneJS": ("Keystone",),
        "MODX": ("MODX CMS", "MODX Revolution", "MODX Revo"),
        "Neos": ("Neos CMS", "TYPO3 Neos"),
        "Omeka": ("Omeka Classic",),
        "SilverStripe": ("Silverstripe CMS",),
        "Textpattern": ("Textpattern CMS",),
        "Typemill": ("Type Mill", "Typemill CMS"),
        "TYPO3": ("TYPO 3", "TYPO3 CMS"),
        "Umbraco": ("Umbraco CMS",),
        "Vvveb CMS": ("Vvveb",),
        "Wagtail": ("Wagtail CMS",),
        "Plone": ("Plone CMS",),
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
EXCLUDED_ALIASES = {
    "data-formats": {
        "hash", "hashes", "raw", "sum", "sums",
        "traveling salesman problem", "travelling salesman problem",
        "robotx.txt", "tab-seperated values",
        "FI Glet Font", "L Tspice Symbol", "c URL Config",
        "OA Sv2 json", "OA Sv2 yaml", "OA Sv3 json", "OA Sv3 yaml",
    },
}
SEPARATED_NAMES = {
    "html-input-types", "html-attributes", "css-properties", "css-pseudo-classes",
    "css-pseudo-elements", "css-functions", "aria-roles", "sql-data-types",
    "git-hooks", "character-encodings", "http-status-names", "http-methods",
    "http-headers", "http-cache-directives", "http-auth-schemes",
}
CAMEL_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
GNU_LICENSE = re.compile(r"((?:A|L)?GPL)-(\d+\.\d+)-(only|or-later)")
VERSIONED_LICENSE = re.compile(r"([A-Za-z][\w-]+)-(\d+(?:\.\d+)+[a-z]?)")


def license_aliases(name):
    if "-" in name:
        yield name.replace("-", " ")
    gnu = GNU_LICENSE.fullmatch(name)
    if gnu:
        family, version, terms = gnu.groups()
        if terms == "only":
            yield f"{family}-{version}"  # Deprecated SPDX ID for this version only.
        short = version.removesuffix(".0")
        if terms == "or-later":
            yield f"{family}-{version}+"
            yield f"{family}v{short}+"
            yield f"{family} v{version} or later"
            yield f"{family} v{short} or later"
        else:
            yield f"{family}v{short} only"
            yield f"{family} v{version} only"
            yield f"{family} v{short} only"
        return

    versioned = VERSIONED_LICENSE.fullmatch(name)
    if versioned:
        family, version = versioned.groups()
        yield f"{family} v{version}"


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
        yield name + "()"
        yield name.casefold() + "()"
        yield "except " + name
        yield "except " + name + ":"
        return
    if slug == "cpu-architectures":
        yield "GOARCH=" + ("386" if name == "x86" else name)
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
        yield from license_aliases(name)
        return

    if slug not in NAMED_CATALOGS and slug not in SEPARATED_NAMES:
        return

    if "'" in name:
        yield name.replace("'", "’")
    if "-" in name:
        yield name.replace("-", "‐")
        yield name.replace("-", "‑")
        if slug == "tree-structures":
            yield name.replace("-", "–")

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
