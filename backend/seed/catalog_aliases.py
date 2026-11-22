"""Alias evidence from the bank's registries and upstream documentation."""

import html
import re
from collections import defaultdict
from encodings import normalize_encoding
from encodings.aliases import aliases as python_codec_aliases


def registered_expansion(identifier, description):
    """Accept a registry expansion when it explicitly names the identifier."""
    description = description.strip()
    expanded = re.fullmatch(r"([\w][\w ./+&-]{4,90}) \(([A-Za-z0-9-]+)\)", description)
    if expanded and expanded[2].casefold() == identifier.casefold():
        return [expanded[1]]
    if re.fullmatch(r"[A-Za-z]{3,8}", identifier) and re.fullmatch(r"[A-Za-z]+(?:[ -][A-Za-z]+){2,8}", description):
        initials = "".join(word[0] for word in re.split(r"[ -]", description))
        if initials.casefold() == identifier.casefold():
            return [description]
    return []


def charset_aliases(rows):
    encodings = defaultdict(set)
    supported = set(python_codec_aliases.values())
    overrides = {"Shift_JIS": "shift_jis", "Windows-31J": "cp932"}
    registered = {label.casefold() for name, labels in rows.items() for label in (name, *labels)}
    for name, labels in rows.items():
        if name in overrides:
            encodings[overrides[name]].add(name)
            continue
        for label in (name, *labels):
            key = normalize_encoding(label).lower()
            codec = python_codec_aliases.get(key, key)
            if codec in supported:
                encodings[codec].add(name)

    result = defaultdict(set)
    for spelling, codec in python_codec_aliases.items():
        if len(encodings[codec]) == 1:
            name = next(iter(encodings[codec]))
            if spelling.startswith("x_mac_") or (name == "TIS-620" and spelling.startswith("iso")):
                continue
            result[name].update(label for label in (spelling, codec) if label.casefold() not in registered)
    return {name: sorted(spellings) for name, spellings in result.items()}


def domain_aliases(name):
    label = name.removeprefix(".")
    labels = [label]
    if not label.isascii():
        labels.append("xn--" + label.encode("punycode").decode("ascii"))
    for spelling in labels:
        yield spelling
        yield spelling + "."
        yield "." + spelling


def powershell_aliases(source):
    aliases = defaultdict(list)
    for spelling, target in re.findall(r'new SessionStateAliasEntry\("([^"]+)", "([^"]+)"', source):
        aliases[target.casefold()].append(spelling)
    return aliases


def nist_aliases(source):
    aliases = defaultdict(list)
    for name, link in re.findall(r'<dt>([^<>\n]+): see <a href="(HTML/[^"]+)">', source, flags=re.IGNORECASE):
        aliases[link].append(html.unescape(name).strip())
    return aliases


def bcd_aliases(name, node):
    support = node["__compat"].get("support", {})
    for browser in support.values():
        for entry in browser if isinstance(browser, list) else [browser]:
            if isinstance(entry, dict):
                if entry.get("alternative_name"):
                    yield entry["alternative_name"]
                if entry.get("prefix"):
                    yield entry["prefix"] + name


def js_member_aliases(owner, name, node):
    # MDN's specification links distinguish static members from prototype members.
    refs = node["__compat"].get("spec_url", [])
    refs = [refs] if isinstance(refs, str) else refs
    yield f"{owner}.{name}"
    yield name + "()"
    anchors = [ref.rsplit("#", 1)[-1].casefold() for ref in refs]
    prototyped = f"sec-{owner.casefold()}.prototype.{name.casefold()}"
    if prototyped in anchors or f"sec-get-{prototyped.removeprefix('sec-')}" in anchors:
        yield f"{owner}.prototype.{name}"
    if prototyped in anchors and name not in {"constructor", "lastIndex", "name"}:
        yield f"{owner}.prototype.{name}()"
